from django.db import models
from django.conf import settings


class Intake(models.Model):
    class TriageLevel(models.TextChoices):
        EMERGENCY = "emergency", "Emergency — seek emergency care now"
        URGENT    = "urgent",    "Urgent — same-day evaluation needed"
        ROUTINE   = "routine",   "Routine — schedule an appointment"
        SELF_CARE = "self_care", "Self-care — monitor and rest"

    class Status(models.TextChoices):
        NEW        = "new",        "New"
        IN_REVIEW  = "in_review",  "In Review"
        ASSIGNED   = "assigned",   "Assigned"
        RESOLVED   = "resolved",   "Resolved"

    patient         = models.ForeignKey(
                          settings.AUTH_USER_MODEL,
                          on_delete=models.PROTECT,
                          related_name="intakes",
                      )
    chief_complaint = models.TextField()
    symptoms        = models.JSONField(default=list)
    severity        = models.PositiveSmallIntegerField(
                          help_text="Patient-reported severity 1–10"
                      )
    duration_hours  = models.PositiveIntegerField()
    red_flags       = models.JSONField(default=list)
    triage_level    = models.CharField(
                          max_length=20,
                          choices=TriageLevel.choices,
                          db_index=True,
                      )
    triage_reason   = models.TextField()
    status          = models.CharField(
                          max_length=20,
                          choices=Status.choices,
                          default=Status.NEW,
                          db_index=True,
                      )
    assigned_to     = models.ForeignKey(
                          settings.AUTH_USER_MODEL,
                          null=True, blank=True,
                          on_delete=models.SET_NULL,
                          related_name="assigned_intakes",
                      )
    created_at      = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at      = models.DateTimeField(auto_now=True)
    notes           = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Intake #{self.pk} — {self.patient} — {self.triage_level}"


class AuditLog(models.Model):
    user       = models.ForeignKey(
                     settings.AUTH_USER_MODEL,
                     null=True, on_delete=models.SET_NULL
                 )
    action     = models.CharField(max_length=100)
    target     = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True)
    detail     = models.JSONField(default=dict)

    class Meta:
        ordering = ["-timestamp"]
