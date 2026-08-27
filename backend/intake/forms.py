from django import forms

SYMPTOM_CHOICES = [
    ("chest pain",         "Chest pain or pressure"),
    ("shortness of breath","Shortness of breath"),
    ("fever",              "Fever"),
    ("cough",              "Cough"),
    ("fatigue",            "Fatigue"),
    ("headache",           "Headache"),
    ("nausea",             "Nausea or vomiting"),
    ("dizziness",          "Dizziness"),
    ("sore throat",        "Sore throat"),
    ("abdominal pain",     "Abdominal pain"),
    ("rash",               "Rash or skin changes"),
    ("joint pain",         "Joint or muscle pain"),
]


class IntakeForm(forms.Form):
    chief_complaint = forms.CharField(
        label="Describe your main concern",
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "What brings you in today?"}),
    )
    symptoms = forms.MultipleChoiceField(
        label="Select all symptoms that apply",
        choices=SYMPTOM_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    severity = forms.IntegerField(
        label="Overall severity (1 = minimal, 10 = worst possible)",
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={"type": "range", "min": 1, "max": 10, "step": 1}),
    )
    duration_hours = forms.IntegerField(
        label="How long have you had these symptoms (hours)?",
        min_value=1,
    )
    consent = forms.BooleanField(
        label=(
            "I understand this is a routing tool only and NOT a medical diagnosis. "
            "I consent to a clinician reviewing my information."
        ),
        required=True,
    )
