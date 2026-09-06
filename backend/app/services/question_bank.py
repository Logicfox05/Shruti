import os
import json
import random
from typing import List, Dict, Any
from ..config import DATA_DIR, FINANCE_QUESTIONS_COUNT, IQ_ADAPTABILITY_QUESTIONS_COUNT


def _load_pool(primary: str, fallback: str) -> List[Dict[str, Any]]:
    """Loads a question pool, falling back to a secondary file if the primary is missing."""
    file_path = os.path.join(DATA_DIR, primary)
    if not os.path.exists(file_path):
        file_path = os.path.join(DATA_DIR, fallback)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _dedupe_by_text(pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Collapses the pool to distinct questions keyed by question_text.

    The repositories contain the same question many times over (only the id and a
    "(Case Study N)" topic suffix differ). Sampling raw rows would deliver the same
    question two or three times in one sitting and count it multiple times toward the
    score. Deduplicating first guarantees every delivered question is distinct, so the
    percentage reflects distinct competencies, not repeated ones.
    """
    seen = set()
    unique = []
    for q in pool:
        key = (q.get("question_text") or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(q)
    return unique


class QuestionBankService:
    @staticmethod
    def shuffle_options(q: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a copy of the question with its four options randomly re-ordered and
        correct_option remapped to wherever the correct answer landed.

        The source repositories store the correct answer as option "A" for every single
        question. Without this step the answer is always in the first slot, so the score
        measures "did the candidate click A" rather than knowledge, and a fixed-position
        guesser scores 100%. Shuffling per session strips all signal from answer position.
        """
        letters = ["A", "B", "C", "D"]
        correct_letter = (q.get("correct_option") or "A").strip().upper()
        by_letter = {
            "A": q.get("option_a", ""),
            "B": q.get("option_b", ""),
            "C": q.get("option_c", ""),
            "D": q.get("option_d", ""),
        }
        correct_text = by_letter.get(correct_letter, by_letter["A"])

        texts = [by_letter["A"], by_letter["B"], by_letter["C"], by_letter["D"]]
        random.shuffle(texts)

        new_correct = "A"
        for i, text in enumerate(texts):
            if text == correct_text:
                new_correct = letters[i]
                break

        out = dict(q)
        out["option_a"], out["option_b"], out["option_c"], out["option_d"] = texts
        out["correct_option"] = new_correct
        return out

    @staticmethod
    def get_random_finance_questions(count: int = FINANCE_QUESTIONS_COUNT, role: str = "Accountant") -> List[Dict[str, Any]]:
        """
        Draws up to `count` (48) DISTINCT, randomized Indian Accounts & Finance questions
        from the finance repository on every candidate login.
        """
        pool = _dedupe_by_text(_load_pool("repository_finance_750.json", "questions_accountant.json"))
        return random.sample(pool, min(count, len(pool)))

    @staticmethod
    def get_random_iq_questions(count: int = IQ_ADAPTABILITY_QUESTIONS_COUNT) -> List[Dict[str, Any]]:
        """
        Draws up to `count` (16) DISTINCT, randomized IQ & Workplace Adaptability questions
        from the IQ repository on every candidate login.
        """
        pool = _dedupe_by_text(_load_pool("repository_iq_250.json", "questions_iq_adaptability.json"))
        return random.sample(pool, min(count, len(pool)))

    @staticmethod
    def get_role_questions(role: str) -> List[Dict[str, Any]]:
        """Legacy helper for backward compatibility."""
        return QuestionBankService.get_random_finance_questions(FINANCE_QUESTIONS_COUNT, role)

    @staticmethod
    def get_iq_adaptability_questions() -> List[Dict[str, Any]]:
        """Legacy helper for backward compatibility."""
        return QuestionBankService.get_random_iq_questions(IQ_ADAPTABILITY_QUESTIONS_COUNT)
