"""Pure deterministic scoring shared by production grading and evaluation."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class DeterministicAssessmentScore:
    score: Decimal
    passed: bool


def calculate_assessment_score(
    *, correct_answers: int, total_questions: int, pass_threshold: int
) -> DeterministicAssessmentScore:
    if (
        isinstance(correct_answers, bool)
        or isinstance(total_questions, bool)
        or isinstance(pass_threshold, bool)
        or not isinstance(correct_answers, int)
        or not isinstance(total_questions, int)
        or not isinstance(pass_threshold, int)
        or total_questions <= 0
        or not 0 <= correct_answers <= total_questions
        or not 1 <= pass_threshold <= 100
    ):
        raise ValueError('Deterministic assessment score inputs are invalid')

    score = (
        Decimal(correct_answers * 100) / Decimal(total_questions)
    ).quantize(Decimal('0.01'))
    return DeterministicAssessmentScore(
        score=score,
        passed=score >= Decimal(pass_threshold),
    )
