import os
import glob
import json
import random
from typing import List, Dict, Any, Set
from sqlalchemy import func

from ..config import DATA_DIR
from .question_bank import QuestionBankService

# --------------------------------------------------------------------------
# Adaptive assessment engine
#
# The exam is served in batches of 5. Each subject runs its own difficulty
# ladder; after every batch the candidate is promoted a tier if they score
# >=75% (>=4/5), demoted if they score <=40% (<=2/5), and held otherwise.
# All of this happens server-side and is invisible to the candidate.
#
#   finance  -> Basic -> Intermediate -> Advanced   (48 questions)
#   iq       -> Basic -> Advanced                   (16 questions; bank has NO IQ 'Intermediate')
#   resume   -> fixed 16 (not adaptive), from questions generated at registration
#
# Total per session = 48 + 16 + 16 = 80.
# --------------------------------------------------------------------------

BATCH_SIZE = 5
PROMOTE_RATIO = 0.75   # >= 4 of 5 promotes a tier
DEMOTE_RATIO = 0.40    # <= 2 of 5 demotes a tier

FINANCE_LADDER = ["Basic", "Intermediate", "Advanced"]
IQ_LADDER = ["Basic", "Advanced"]

SECTION_ORDER = ["finance", "iq", "resume"]
SECTION_QUOTA = {"finance": 48, "iq": 16, "resume": 16}

_CATEGORY = {"finance": "Accounting & Finance", "iq": "IQ & Adaptability"}

# Glob patterns for the bank files, keyed by (section, tier). Files are split into
# parts (e.g. bank_fin_basic_1.json) and merged at load time.
_FILE_MAP = {
    ("finance", "Basic"): "bank_fin_basic*.json",
    ("finance", "Intermediate"): "bank_fin_inter*.json",
    ("finance", "Advanced"): "bank_fin_adv*.json",
    ("iq", "Basic"): "bank_iq_basic*.json",
    ("iq", "Advanced"): "bank_iq_adv*.json",
}

_pool_cache: Dict[Any, List[Dict[str, Any]]] = {}


def _load_pool(section: str, tier: str) -> List[Dict[str, Any]]:
    """Loads and caches the (section, tier) question pool from the bank files,
    annotating each item with its broad category, tier and topic."""
    key = (section, tier)
    if key in _pool_cache:
        return _pool_cache[key]

    items: List[Dict[str, Any]] = []
    pattern = _FILE_MAP.get(key)
    if pattern:
        for path in sorted(glob.glob(os.path.join(DATA_DIR, pattern))):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    items.extend(json.load(f))
            except Exception:
                continue

    for it in items:
        it["category"] = _CATEGORY[section]
        it["cognitive_level"] = tier
        it.setdefault("topic", it.get("tag", "General"))
        it.setdefault("explanation", "")

    _pool_cache[key] = items
    return items


def ladder_for(section: str) -> List[str]:
    return FINANCE_LADDER if section == "finance" else IQ_LADDER


def next_tier(section: str, current_tier: str, correct: int, total: int) -> str:
    """Decide the tier for the NEXT batch of the same section from the last batch's score."""
    ladder = ladder_for(section)
    idx = ladder.index(current_tier) if current_tier in ladder else 0
    ratio = (correct / total) if total else 0.0
    if ratio >= PROMOTE_RATIO and idx < len(ladder) - 1:
        return ladder[idx + 1]
    if ratio <= DEMOTE_RATIO and idx > 0:
        return ladder[idx - 1]
    return ladder[idx]


def draw_batch(section: str, tier: str, exclude_texts: Set[str], n: int = BATCH_SIZE) -> List[Dict[str, Any]]:
    """Return up to n distinct, unseen questions at `tier`. If that tier is
    exhausted for this session, fall back to the nearest tiers in the ladder so a
    batch is always filled where the bank allows."""
    ladder = ladder_for(section)
    idx = ladder.index(tier) if tier in ladder else 0
    # Requested tier first, then remaining tiers ordered by distance.
    tier_order = sorted(ladder, key=lambda t: abs(ladder.index(t) - idx))

    chosen: List[Dict[str, Any]] = []
    seen_texts = set(exclude_texts)
    for t in tier_order:
        pool = [q for q in _load_pool(section, t) if q["question_text"] not in seen_texts]
        random.shuffle(pool)
        for q in pool:
            chosen.append(q)
            seen_texts.add(q["question_text"])
            if len(chosen) >= n:
                return chosen[:n]
    return chosen[:n]


class AdaptiveService:
    """Orchestrates batch serving and grading. Each public method commits its own
    writes so routers stay thin."""

    @staticmethod
    def _next_qnum(session, db) -> int:
        from ..models import SessionQuestion
        mx = db.query(func.max(SessionQuestion.question_number)).filter(
            SessionQuestion.session_id == session.id
        ).scalar()
        return (mx or 0) + 1

    @staticmethod
    def _served_count(session, section: str) -> int:
        return {
            "finance": session.finance_served or 0,
            "iq": session.iq_served or 0,
            "resume": session.resume_served or 0,
        }[section]

    @staticmethod
    def _bump_served(session, section: str, k: int):
        if section == "finance":
            session.finance_served = (session.finance_served or 0) + k
        elif section == "iq":
            session.iq_served = (session.iq_served or 0) + k
        elif section == "resume":
            session.resume_served = (session.resume_served or 0) + k

    @staticmethod
    def _persist_batch(session, db, batch: List[Dict[str, Any]], is_resume: bool):
        from ..models import SessionQuestion
        qnum = AdaptiveService._next_qnum(session, db)
        created = []
        for q in batch:
            qs = QuestionBankService.shuffle_options(q)  # per-session option shuffle
            sq = SessionQuestion(
                session_id=session.id,
                question_number=qnum,
                category=qs.get("category", "General"),
                topic=(qs.get("topic") or qs.get("tag") or "General"),
                cognitive_level=qs.get("cognitive_level", "Basic"),
                is_resume_based=is_resume,
                question_text=qs["question_text"],
                option_a=qs["option_a"],
                option_b=qs["option_b"],
                option_c=qs["option_c"],
                option_d=qs["option_d"],
                correct_option=qs["correct_option"],
                explanation=qs.get("explanation", ""),
            )
            db.add(sq)
            created.append(sq)
            qnum += 1
        session.current_batch_size = len(created)
        return created

    @staticmethod
    def _draw_and_persist(session, db, section: str, tier: str, exclude_texts: Set[str]):
        remaining = SECTION_QUOTA[section] - AdaptiveService._served_count(session, section)
        if remaining <= 0:
            return []
        k = min(BATCH_SIZE, remaining)
        if section == "resume":
            pending = json.loads(session.pending_resume or "[]")
            start = AdaptiveService._served_count(session, "resume")
            batch = pending[start:start + k]
            created = AdaptiveService._persist_batch(session, db, batch, is_resume=True)
        else:
            batch = draw_batch(section, tier, exclude_texts, k)
            created = AdaptiveService._persist_batch(session, db, batch, is_resume=False)
        AdaptiveService._bump_served(session, section, len(created))
        return created

    @staticmethod
    def ensure_first_batch(session, db):
        """Serve the opening batch (finance, Basic) if nothing has been served yet."""
        from ..models import SessionQuestion
        already = db.query(SessionQuestion).filter(SessionQuestion.session_id == session.id).count()
        if already > 0:
            return []
        session.current_section = "finance"
        session.current_tier = "Basic"
        created = AdaptiveService._draw_and_persist(session, db, "finance", "Basic", set())
        db.commit()
        return created

    @staticmethod
    def grade_and_advance(session, db):
        """Grade the outstanding batch, update the tier, and serve the next batch
        (or advance to the next section, or finish). Returns the newly served rows."""
        from ..models import SessionQuestion
        served_qs = db.query(SessionQuestion).filter(
            SessionQuestion.session_id == session.id
        ).order_by(SessionQuestion.question_number).all()

        k = session.current_batch_size or 0
        batch = served_qs[-k:] if k else []
        correct = 0
        for q in batch:
            sel = (q.selected_option or "").strip().upper()
            cor = (q.correct_option or "").strip().upper()
            q.is_correct = bool(sel and sel == cor)
            if q.is_correct:
                correct += 1
        total = len(batch)

        section = session.current_section
        exclude_texts = {q.question_text for q in served_qs}

        # Within an adaptive section that still has quota left, update the tier for the next batch.
        if section in ("finance", "iq") and AdaptiveService._served_count(session, section) < SECTION_QUOTA[section]:
            session.current_tier = next_tier(section, session.current_tier, correct, total)

        created = AdaptiveService._serve_next(session, db, exclude_texts)
        db.commit()
        return created

    @staticmethod
    def _serve_next(session, db, exclude_texts: Set[str]):
        section = session.current_section
        # Still room in the current section -> serve the next batch within it.
        if section in SECTION_QUOTA and AdaptiveService._served_count(session, section) < SECTION_QUOTA[section]:
            return AdaptiveService._draw_and_persist(session, db, section, session.current_tier, exclude_texts)

        # Otherwise advance to the next section that still has quota.
        nxt = AdaptiveService._next_section(section)
        while nxt is not None and AdaptiveService._served_count(session, nxt) >= SECTION_QUOTA[nxt]:
            nxt = AdaptiveService._next_section(nxt)
        if nxt is None:
            session.current_section = "complete"
            session.current_batch_size = 0
            return []
        session.current_section = nxt
        session.current_tier = "Basic"
        return AdaptiveService._draw_and_persist(session, db, nxt, "Basic", exclude_texts)

    @staticmethod
    def _next_section(section: str):
        if section not in SECTION_ORDER:
            return SECTION_ORDER[0]
        i = SECTION_ORDER.index(section)
        return SECTION_ORDER[i + 1] if i + 1 < len(SECTION_ORDER) else None
