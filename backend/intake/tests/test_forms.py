from django.test import TestCase
from intake.forms import IntakeForm


class IntakeFormValidationTests(TestCase):
    def _valid_data(self, **overrides):
        base = {
            "chief_complaint": "Sore throat and mild fever",
            "symptoms": ["sore throat", "fever"],
            "severity": 5,
            "duration_hours": 12,
            "consent": True,
        }
        base.update(overrides)
        return base

    def test_valid_form(self):
        form = IntakeForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_severity_below_1_invalid(self):
        form = IntakeForm(data=self._valid_data(severity=0))
        self.assertFalse(form.is_valid())
        self.assertIn("severity", form.errors)

    def test_severity_above_10_invalid(self):
        form = IntakeForm(data=self._valid_data(severity=11))
        self.assertFalse(form.is_valid())
        self.assertIn("severity", form.errors)

    def test_empty_chief_complaint_invalid(self):
        form = IntakeForm(data=self._valid_data(chief_complaint=""))
        self.assertFalse(form.is_valid())

    def test_consent_required(self):
        form = IntakeForm(data=self._valid_data(consent=False))
        self.assertFalse(form.is_valid())
        self.assertIn("consent", form.errors)

    def test_duration_zero_invalid(self):
        form = IntakeForm(data=self._valid_data(duration_hours=0))
        self.assertFalse(form.is_valid())
