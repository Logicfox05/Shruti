from typing import List
from ..models import AssessmentSession, SessionQuestion

class ScoringService:
    @staticmethod
    def calculate_session_score(session: AssessmentSession, questions: List[SessionQuestion]):
        total_questions = len(questions)
        if total_questions == 0:
            session.total_score = 0.0
            session.max_score = 0.0
            session.percentage = 0.0
            return 0.0

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
        session.max_score = float(total_questions)
        session.percentage = round((correct_count / total_questions) * 100, 2)
        return session.percentage
