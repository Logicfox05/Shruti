from typing import List
from ..models import AssessmentSession, SessionQuestion
from .adaptive_engine import SECTION_QUOTA

# The exam is ALWAYS scored out of its full length (48 finance + 16 IQ + 16 resume = 80).
# Questions the candidate never reached (submitted early / timed out) or left blank are
# scored as wrong, so answering only a handful of questions cannot inflate the percentage.
TOTAL_QUESTIONS = sum(SECTION_QUOTA.values())


class ScoringService:
    @staticmethod
    def calculate_session_score(session: AssessmentSession, questions: List[SessionQuestion]):
        correct_count = 0
        for q in questions:
            selected = (q.selected_option or "").strip().upper()
            correct = (q.correct_option or "").strip().upper()
            # A question is correct only when the candidate actually selected an option
            # and it matches the stored (post-shuffle) correct letter. Unanswered = wrong.
            if selected and selected == correct:
                q.is_correct = True
                correct_count += 1
            else:
                q.is_correct = False

        session.total_score = float(correct_count)
        session.max_score = float(TOTAL_QUESTIONS)
        session.percentage = round((correct_count / TOTAL_QUESTIONS) * 100, 2)
        return session.percentage
