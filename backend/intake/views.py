from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.core.paginator import Paginator

from .forms import IntakeForm
from .models import Intake, AuditLog
from .triage import determine_triage


def _log(request, action, target="", detail=None):
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        target=target,
        ip_address=request.META.get("REMOTE_ADDR"),
        detail=detail or {},
    )


def is_clinician(user):
    return user.is_authenticated and (user.is_staff or user.groups.filter(name="Clinicians").exists())


@method_decorator(login_required, name="dispatch")
class IntakeFormView(View):
    template_name = "intake/form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": IntakeForm()})

    def post(self, request):
        form = IntakeForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        data = form.cleaned_data
        result = determine_triage(
            symptoms=data["symptoms"],
            chief_complaint=data["chief_complaint"],
            severity=data["severity"],
            duration_hours=data["duration_hours"],
        )
        intake = Intake.objects.create(
            patient=request.user,
            chief_complaint=data["chief_complaint"],
            symptoms=data["symptoms"],
            severity=data["severity"],
            duration_hours=data["duration_hours"],
            red_flags=[],
            triage_level=result.level,
            triage_reason=result.reason,
        )
        _log(request, "intake_submitted", f"Intake#{intake.pk}", {"triage": result.level})
        return redirect("intake:result", pk=intake.pk)


@login_required
def intake_result(request, pk):
    intake = get_object_or_404(Intake, pk=pk, patient=request.user)
    return render(request, "intake/result.html", {"intake": intake})


@user_passes_test(is_clinician)
def clinician_queue(request):
    status_filter = request.GET.get("status", "new")
    qs = Intake.objects.filter(status=status_filter).select_related("patient", "assigned_to")
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page", 1))
    _log(request, "queue_viewed", detail={"status": status_filter})
    return render(request, "clinician/queue.html", {"page": page, "status_filter": status_filter})


@user_passes_test(is_clinician)
def queue_poll(request):
    """JSON endpoint for front-end polling — returns count of new intakes."""
    count = Intake.objects.filter(status="new").count()
    return JsonResponse({"new_count": count})


@user_passes_test(is_clinician)
def intake_update_status(request, pk):
    if request.method != "POST":
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(["POST"])
    intake = get_object_or_404(Intake, pk=pk)
    new_status = request.POST.get("status")
    if new_status in dict(Intake.Status.choices):
        old = intake.status
        intake.status = new_status
        if new_status == "assigned":
            intake.assigned_to = request.user
        intake.save()
        _log(request, "status_changed", f"Intake#{pk}", {"from": old, "to": new_status})
    return redirect("intake:queue")
