"""
Deterministic, rule-based triage engine.
All logic is pure Python — fully unit-testable without Django.
DISCLAIMER: This is a routing aid only. It is NOT a medical diagnosis.
"""
from dataclasses import dataclass
from typing import Literal

TriageLevel = Literal["emergency", "urgent", "routine", "self_care"]

RED_FLAG_TERMS = frozenset([
    "chest pain", "chest pressure", "shortness of breath",
    "difficulty breathing", "sudden severe headache", "worst headache",
    "loss of consciousness", "fainting", "stroke symptoms", "facial drooping",
    "arm weakness", "slurred speech", "coughing blood", "vomiting blood",
    "severe abdominal pain", "suicidal", "overdose",
])


@dataclass(frozen=True)
class TriageResult:
    level: TriageLevel
    reason: str
    disclaimer: str = (
        "⚠️ This is a routing suggestion only and is NOT a medical diagnosis. "
        "A licensed clinician will review your intake and may contact you. "
        "If you are in immediate danger, call 911."
    )


def _detect_red_flags(symptoms: list[str], chief_complaint: str) -> list[str]:
    text = " ".join(symptoms + [chief_complaint]).lower()
    return [flag for flag in RED_FLAG_TERMS if flag in text]


def determine_triage(
    *,
    symptoms: list[str],
    chief_complaint: str,
    severity: int,
    duration_hours: int,
) -> TriageResult:
    """
    Args:
        symptoms: list of symptom strings from the intake form
        chief_complaint: free-text chief complaint
        severity: 1-10 patient-reported severity
        duration_hours: how long symptoms have been present
    Returns:
        TriageResult with level and plain-language reason
    """
    if not (1 <= severity <= 10):
        raise ValueError(f"severity must be 1–10, got {severity}")

    detected_flags = _detect_red_flags(symptoms, chief_complaint)
    if detected_flags:
        return TriageResult(
            level="emergency",
            reason=(
                "Your responses include symptoms that may require emergency care. "
                "Please call 911 or go to the nearest emergency room immediately."
            ),
        )

    if severity >= 8:
        return TriageResult(
            level="urgent",
            reason="High severity score indicates prompt evaluation today is appropriate.",
        )

    if severity >= 6 and duration_hours >= 24:
        return TriageResult(
            level="urgent",
            reason="Moderate-to-high severity persisting over 24 hours warrants same-day care.",
        )

    if severity >= 4:
        return TriageResult(
            level="routine",
            reason="Symptoms are moderate. Scheduling a clinician appointment is recommended.",
        )

    return TriageResult(
        level="self_care",
        reason="Symptoms appear mild. Rest, hydration, and OTC care may be sufficient. Monitor closely.",
    )
