import pytest
from intake.triage import determine_triage, TriageResult


class TestEmergencyTriage:
    def test_red_flag_chest_pain(self):
        result = determine_triage(
            symptoms=["chest pain"],
            chief_complaint="",
            severity=5,
            duration_hours=1,
        )
        assert result.level == "emergency"

    def test_red_flag_in_chief_complaint(self):
        result = determine_triage(
            symptoms=[],
            chief_complaint="I have the worst headache of my life",
            severity=3,
            duration_hours=2,
        )
        assert result.level == "emergency"


class TestUrgentTriage:
    def test_high_severity_alone(self):
        result = determine_triage(
            symptoms=["fever", "fatigue"],
            chief_complaint="fever",
            severity=8,
            duration_hours=6,
        )
        assert result.level == "urgent"

    def test_moderate_severity_long_duration(self):
        result = determine_triage(
            symptoms=["cough"],
            chief_complaint="persistent cough",
            severity=6,
            duration_hours=36,
        )
        assert result.level == "urgent"

    def test_moderate_severity_short_duration_is_not_urgent(self):
        result = determine_triage(
            symptoms=["cough"],
            chief_complaint="cough",
            severity=6,
            duration_hours=12,
        )
        assert result.level == "routine"


class TestRoutineTriage:
    def test_moderate_severity(self):
        result = determine_triage(
            symptoms=["mild headache"],
            chief_complaint="headache",
            severity=5,
            duration_hours=2,
        )
        assert result.level == "routine"


class TestSelfCareTriage:
    def test_low_severity(self):
        result = determine_triage(
            symptoms=["sneezing"],
            chief_complaint="runny nose",
            severity=2,
            duration_hours=1,
        )
        assert result.level == "self_care"


class TestValidation:
    def test_severity_out_of_range_raises(self):
        with pytest.raises(ValueError):
            determine_triage(
                symptoms=[],
                chief_complaint="",
                severity=11,
                duration_hours=1,
            )

    def test_disclaimer_always_present(self):
        result = determine_triage(
            symptoms=[],
            chief_complaint="sore throat",
            severity=3,
            duration_hours=2,
        )
        assert "NOT a medical diagnosis" in result.disclaimer
