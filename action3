#!/usr/bin/env bash
set -euo pipefail
ROOT="$HOME/SACS-MMC-JMHT/telehealth-triage"
B="$ROOT/backend"

# ── directories ────────────────────────────────────────────────────
mkdir -p \
  "$ROOT/.github/workflows" \
  "$B/templates/intake" \
  "$B/templates/clinician" \
  "$B/templates/registration" \
  "$B/static/css" \
  "$B/static/js" \
  "$B/static/icons" \
  "$ROOT/docs" \
  "$ROOT/scripts"

touch "$B/users/__init__.py" "$B/users/apps.py"
touch "$B/audit/__init__.py" "$B/audit/apps.py"

# ── users/apps.py ──────────────────────────────────────────────────
cat > "$B/users/apps.py" << 'EOF'
from django.apps import AppConfig
class UsersConfig(AppConfig):
    name = "users"
EOF

# ── audit/apps.py ──────────────────────────────────────────────────
cat > "$B/audit/apps.py" << 'EOF'
from django.apps import AppConfig
class AuditConfig(AppConfig):
    name = "audit"
EOF

# ── templates/base.html ────────────────────────────────────────────
cat > "$B/templates/base.html" << 'TMPL'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <meta name="theme-color" content="#0077cc"/>
  <link rel="manifest" href="/static/manifest.json"/>
  <title>{% block title %}TeleHealth Triage{% endblock %}</title>
  <link rel="stylesheet" href="/static/css/main.css"/>
</head>
<body>
<header class="site-header">
  <a class="brand" href="/">TeleHealth Triage</a>
  {% if user.is_authenticated %}
  <nav>
    {% if user.is_staff %}<a href="/intake/queue/">Queue</a>
    {% else %}<a href="/intake/">New Intake</a>{% endif %}
    <form method="post" action="/accounts/logout/" style="display:inline">
      {% csrf_token %}
      <button class="btn-link">Log Out</button>
    </form>
  </nav>
  {% endif %}
</header>
<main class="container">
  {% if messages %}
  <ul class="messages">
    {% for m in messages %}<li class="msg-{{ m.tags }}">{{ m }}</li>{% endfor %}
  </ul>
  {% endif %}
  {% block content %}{% endblock %}
</main>
<script src="/static/js/queue_poll.js" defer></script>
</body>
</html>
TMPL

# ── templates/registration/login.html ─────────────────────────────
cat > "$B/templates/registration/login.html" << 'TMPL'
{% extends "base.html" %}
{% block title %}Log In — TeleHealth Triage{% endblock %}
{% block content %}
<section class="card" style="max-width:400px;margin:2rem auto">
  <h1>Log In</h1>
  <form method="post" novalidate>
    {% csrf_token %}
    {% for field in form %}
    <div class="field {% if field.errors %}field--error{% endif %}">
      <label for="{{ field.id_for_label }}">{{ field.label }}</label>
      {{ field }}
      {% for err in field.errors %}<span class="field-error">{{ err }}</span>{% endfor %}
    </div>
    {% endfor %}
    <button type="submit" class="btn btn--primary" style="width:100%">Log In</button>
  </form>
</section>
{% endblock %}
TMPL

# ── templates/intake/form.html ─────────────────────────────────────
cat > "$B/templates/intake/form.html" << 'TMPL'
{% extends "base.html" %}
{% block title %}Patient Intake — TeleHealth Triage{% endblock %}
{% block content %}
<section class="intake-form card">
  <h1>Complete Your Intake</h1>
  <div class="disclaimer">
    &#9888; <strong>Routing tool only.</strong>
    Not a diagnosis. Emergency? Call <strong>911</strong>.
  </div>
  <form method="post" novalidate>
    {% csrf_token %}
    {% for field in form %}
    <div class="field {% if field.errors %}field--error{% endif %}">
      <label for="{{ field.id_for_label }}">{{ field.label }}</label>
      {{ field }}
      {% if field.name == "severity" %}
        <output id="severity-output" style="font-weight:700;margin-left:.5rem">5</output>
      {% endif %}
      {% for err in field.errors %}<span class="field-error">{{ err }}</span>{% endfor %}
    </div>
    {% endfor %}
    <button type="submit" class="btn btn--primary" style="width:100%">
      Submit Intake &#8594;
    </button>
  </form>
</section>
<script>
  const s = document.querySelector('input[name="severity"]');
  const o = document.getElementById("severity-output");
  if (s && o) { o.value = s.value; s.addEventListener("input", () => o.value = s.value); }
</script>
{% endblock %}
TMPL

# ── templates/intake/result.html ──────────────────────────────────
cat > "$B/templates/intake/result.html" << 'TMPL'
{% extends "base.html" %}
{% block title %}Your Triage Result — TeleHealth Triage{% endblock %}
{% block content %}
<section class="triage-result card triage-{{ intake.triage_level }}">
  <h1>Your Routing Recommendation</h1>
  <div class="triage-badge">{{ intake.get_triage_level_display }}</div>
  <p class="triage-reason">{{ intake.triage_reason }}</p>
  <div class="disclaimer">
    &#9888; Routing suggestion only &mdash; <strong>NOT a medical diagnosis</strong>.
    A clinician will review your intake. If in danger, call 911.
  </div>
  <dl class="summary">
    <dt>Severity reported</dt><dd>{{ intake.severity }}/10</dd>
    <dt>Duration</dt><dd>{{ intake.duration_hours }} hour(s)</dd>
    <dt>Submitted</dt><dd>{{ intake.created_at }}</dd>
  </dl>
  <a href="/intake/" class="btn">Submit another intake</a>
</section>
{% endblock %}
TMPL

# ── templates/clinician/queue.html ────────────────────────────────
cat > "$B/templates/clinician/queue.html" << 'TMPL'
{% extends "base.html" %}
{% block title %}Clinician Queue — TeleHealth Triage{% endblock %}
{% block content %}
<section class="queue">
  <h1>Intake Queue <span class="new-badge" id="new-count"></span></h1>
  <nav class="queue-tabs">
    <a href="?status=new"       class="tab {% if status_filter == 'new' %}tab--active{% endif %}">New</a>
    <a href="?status=in_review" class="tab {% if status_filter == 'in_review' %}tab--active{% endif %}">In Review</a>
    <a href="?status=assigned"  class="tab {% if status_filter == 'assigned' %}tab--active{% endif %}">Assigned</a>
    <a href="?status=resolved"  class="tab {% if status_filter == 'resolved' %}tab--active{% endif %}">Resolved</a>
  </nav>
  <div class="table-wrap">
    <table class="queue-table">
      <thead>
        <tr>
          <th>#</th><th>Patient</th><th>Triage</th>
          <th>Severity</th><th>Submitted</th><th>Assigned</th><th>Status</th>
        </tr>
      </thead>
      <tbody>
        {% for intake in page %}
        <tr class="row-{{ intake.triage_level }}">
          <td data-label="#">{{ intake.pk }}</td>
          <td data-label="Patient">{{ intake.patient.get_full_name|default:intake.patient.username }}</td>
          <td data-label="Triage">
            <span class="badge-{{ intake.triage_level }}">{{ intake.get_triage_level_display }}</span>
          </td>
          <td data-label="Severity">{{ intake.severity }}/10</td>
          <td data-label="Submitted">{{ intake.created_at|date:"M d H:i" }}</td>
          <td data-label="Assigned">{{ intake.assigned_to|default:"&mdash;" }}</td>
          <td data-label="Status">
            <form method="post" action="/intake/{{ intake.pk }}/status/">
              {% csrf_token %}
              <select name="status" class="status-select" onchange="this.form.submit()">
                {% for val, label in intake.Status.choices %}
                <option value="{{ val }}" {% if intake.status == val %}selected{% endif %}>{{ label }}</option>
                {% endfor %}
              </select>
            </form>
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="7" style="text-align:center;padding:2rem">No intakes in this status.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% if page.has_other_pages %}
  <nav class="pagination">
    {% if page.has_previous %}
      <a href="?status={{ status_filter }}&page={{ page.previous_page_number }}">&larr; Prev</a>
    {% endif %}
    Page {{ page.number }} of {{ page.paginator.num_pages }}
    {% if page.has_next %}
      <a href="?status={{ status_filter }}&page={{ page.next_page_number }}">Next &rarr;</a>
    {% endif %}
  </nav>
  {% endif %}
</section>
{% endblock %}
TMPL

# ── static/css/main.css ────────────────────────────────────────────
cat > "$B/static/css/main.css" << 'EOF'
:root {
  --c-primary:   #0077cc;
  --c-emergency: #d32f2f;
  --c-urgent:    #f57c00;
  --c-routine:   #388e3c;
  --c-self-care: #1565c0;
  --c-bg:        #f5f7fa;
  --c-card:      #ffffff;
  --c-text:      #1a1a2e;
  --radius:      8px;
  --shadow:      0 2px 8px rgba(0,0,0,.12);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:var(--c-bg);color:var(--c-text);line-height:1.5}
.site-header{background:var(--c-primary);color:#fff;padding:.75rem 1rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem}
.site-header .brand{color:#fff;font-weight:700;text-decoration:none;font-size:1.1rem}
.site-header nav a{color:#fff;margin-left:1rem;text-decoration:none;font-size:.9rem}
.btn-link{background:none;border:none;color:#fff;cursor:pointer;font-size:.9rem;margin-left:1rem;text-decoration:underline}
.container{max-width:960px;margin:0 auto;padding:1rem}
.card{background:var(--c-card);border-radius:var(--radius);box-shadow:var(--shadow);padding:1.5rem;margin-top:1rem}
.field{margin-bottom:1.25rem}
.field label{display:block;font-weight:600;margin-bottom:.35rem}
.field input,.field textarea,.field select{width:100%;padding:.5rem .75rem;border:1px solid #ccc;border-radius:var(--radius);font-size:1rem}
.field input[type="range"]{padding:0;height:44px;cursor:pointer}
.field--error input,.field--error textarea{border-color:var(--c-emergency)}
.field-error{color:var(--c-emergency);font-size:.85rem;margin-top:.2rem;display:block}
.disclaimer{background:#fff8e1;border-left:4px solid var(--c-urgent);padding:.75rem 1rem;margin-bottom:1rem;border-radius:var(--radius);font-size:.9rem}
.btn{display:inline-block;padding:.6rem 1.4rem;border-radius:var(--radius);border:2px solid var(--c-primary);color:var(--c-primary);background:transparent;cursor:pointer;font-size:1rem;text-decoration:none;transition:background .15s,color .15s}
.btn--primary{background:var(--c-primary);color:#fff;border-color:var(--c-primary)}
.btn--primary:hover{background:#005fa3}
.triage-badge{font-size:1.4rem;font-weight:700;padding:.5rem 1rem;border-radius:var(--radius);display:inline-block;margin:1rem 0}
.triage-emergency .triage-badge{background:var(--c-emergency);color:#fff}
.triage-urgent    .triage-badge{background:var(--c-urgent);color:#fff}
.triage-routine   .triage-badge{background:var(--c-routine);color:#fff}
.triage-self_care .triage-badge{background:var(--c-self-care);color:#fff}
.triage-reason{font-size:1.1rem;margin:.5rem 0 1rem}
dl.summary{display:grid;grid-template-columns:auto 1fr;gap:.25rem .75rem;margin:1rem 0}
dl.summary dt{font-weight:600}
.queue-tabs{display:flex;gap:.5rem;margin:.75rem 0;flex-wrap:wrap}
.tab{padding:.4rem .9rem;border-radius:20px;background:#e0e7ef;text-decoration:none;color:var(--c-text);font-size:.85rem}
.tab--active{background:var(--c-primary);color:#fff}
.table-wrap{overflow-x:auto}
.queue-table{width:100%;border-collapse:collapse;margin-top:.5rem}
.queue-table th,.queue-table td{text-align:left;padding:.6rem .75rem;border-bottom:1px solid #e0e0e0}
.queue-table th{background:#f0f4f8;font-size:.8rem;text-transform:uppercase;letter-spacing:.03em}
.row-emergency{background:#ffebee}
.row-urgent{background:#fff3e0}
.badge-emergency{background:var(--c-emergency);color:#fff;padding:.2rem .5rem;border-radius:4px;font-size:.78rem;white-space:nowrap}
.badge-urgent{background:var(--c-urgent);color:#fff;padding:.2rem .5rem;border-radius:4px;font-size:.78rem;white-space:nowrap}
.badge-routine{background:var(--c-routine);color:#fff;padding:.2rem .5rem;border-radius:4px;font-size:.78rem;white-space:nowrap}
.badge-self_care{background:var(--c-self-care);color:#fff;padding:.2rem .5rem;border-radius:4px;font-size:.78rem;white-space:nowrap}
.status-select{padding:.3rem;border-radius:4px;font-size:.85rem}
.new-badge{font-size:1rem;font-weight:400;color:var(--c-emergency)}
.pagination{margin:1rem 0;display:flex;gap:1rem;align-items:center}
.pagination a{color:var(--c-primary)}
.messages{list-style:none;margin-bottom:1rem}
.messages li{padding:.6rem 1rem;border-radius:var(--radius);margin-bottom:.25rem}
.msg-success{background:#e8f5e9;color:#2e7d32}
.msg-error{background:#ffebee;color:var(--c-emergency)}
@media(max-width:600px){
  .site-header{flex-direction:column;text-align:center}
  .queue-table thead{display:none}
  .queue-table tr{display:block;margin-bottom:.75rem;border:1px solid #ddd;border-radius:var(--radius)}
  .queue-table td{display:flex;justify-content:space-between;padding:.5rem .75rem;border:none;border-bottom:1px solid #f0f0f0}
  .queue-table td::before{content:attr(data-label);font-weight:600;flex-shrink:0;margin-right:.5rem}
  .intake-form{padding:1rem}
}
@media(min-width:1024px){
  .container{padding:2rem}
  .intake-form{max-width:640px}
}
EOF

# ── static/js/queue_poll.js ────────────────────────────────────────
cat > "$B/static/js/queue_poll.js" << 'EOF'
(function(){
  "use strict";
  var badge=document.getElementById("new-count");
  if(!badge)return;
  function poll(){
    fetch("/intake/queue/poll/",{credentials:"same-origin"})
      .then(function(r){return r.ok?r.json():null;})
      .then(function(d){
        if(!d)return;
        badge.textContent=d.new_count>0?"("+d.new_count+" new)":"";
      }).catch(function(){});
  }
  poll();
  setInterval(poll,30000);
})();
EOF

# ── static/manifest.json ──────────────────────────────────────────
cat > "$B/static/manifest.json" << 'EOF'
{
  "name": "TeleHealth Triage",
  "short_name": "Triage",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#f5f7fa",
  "theme_color": "#0077cc",
  "icons": [
    {"src":"/static/icons/icon-192.png","sizes":"192x192","type":"image/png"},
    {"src":"/static/icons/icon-512.png","sizes":"512x512","type":"image/png"}
  ]
}
EOF

# ── intake/tests/test_triage.py ───────────────────────────────────
cat > "$B/intake/tests/test_triage.py" << 'EOF'
import pytest
from intake.triage import determine_triage

class TestEmergency:
    def test_chest_pain_in_symptoms(self):
        r = determine_triage(symptoms=["chest pain"],chief_complaint="",severity=5,duration_hours=1)
        assert r.level == "emergency"
    def test_red_flag_in_chief_complaint(self):
        r = determine_triage(symptoms=[],chief_complaint="worst headache of my life",severity=3,duration_hours=2)
        assert r.level == "emergency"
    def test_suicidal(self):
        r = determine_triage(symptoms=["suicidal"],chief_complaint="",severity=6,duration_hours=1)
        assert r.level == "emergency"
    def test_disclaimer_present(self):
        r = determine_triage(symptoms=["chest pain"],chief_complaint="",severity=5,duration_hours=1)
        assert "NOT a medical diagnosis" in r.disclaimer
    def test_flags_populated(self):
        r = determine_triage(symptoms=["chest pain"],chief_complaint="",severity=5,duration_hours=1)
        assert "chest pain" in r.detected_flags

class TestUrgent:
    def test_high_severity(self):
        r = determine_triage(symptoms=["fever"],chief_complaint="fever",severity=8,duration_hours=6)
        assert r.level == "urgent"
    def test_severity_10(self):
        r = determine_triage(symptoms=[],chief_complaint="pain",severity=10,duration_hours=1)
        assert r.level == "urgent"
    def test_moderate_long_duration(self):
        r = determine_triage(symptoms=["cough"],chief_complaint="cough",severity=6,duration_hours=36)
        assert r.level == "urgent"
    def test_exactly_24h(self):
        r = determine_triage(symptoms=["cough"],chief_complaint="cough",severity=6,duration_hours=24)
        assert r.level == "urgent"
    def test_moderate_short_duration_is_routine(self):
        r = determine_triage(symptoms=["cough"],chief_complaint="cough",severity=6,duration_hours=12)
        assert r.level == "routine"

class TestRoutine:
    def test_moderate_severity(self):
        r = determine_triage(symptoms=["headache"],chief_complaint="headache",severity=5,duration_hours=2)
        assert r.level == "routine"
    def test_severity_4(self):
        r = determine_triage(symptoms=[],chief_complaint="sore throat",severity=4,duration_hours=3)
        assert r.level == "routine"

class TestSelfCare:
    def test_low_severity(self):
        r = determine_triage(symptoms=["sneezing"],chief_complaint="runny nose",severity=2,duration_hours=1)
        assert r.level == "self_care"
    def test_severity_1(self):
        r = determine_triage(symptoms=[],chief_complaint="slight itch",severity=1,duration_hours=1)
        assert r.level == "self_care"

class TestValidation:
    def test_severity_zero_raises(self):
        with pytest.raises(ValueError):
            determine_triage(symptoms=[],chief_complaint="",severity=0,duration_hours=1)
    def test_severity_11_raises(self):
        with pytest.raises(ValueError):
            determine_triage(symptoms=[],chief_complaint="",severity=11,duration_hours=1)
    def test_severity_negative_raises(self):
        with pytest.raises(ValueError):
            determine_triage(symptoms=[],chief_complaint="",severity=-1,duration_hours=1)
EOF

# ── intake/tests/test_forms.py ────────────────────────────────────
cat > "$B/intake/tests/test_forms.py" << 'EOF'
from django.test import TestCase
from intake.forms import IntakeForm

class IntakeFormTests(TestCase):
    def _data(self,**kw):
        d={"chief_complaint":"Sore throat","symptoms":["sore throat"],"severity":5,"duration_hours":12,"consent":True}
        d.update(kw); return d
    def test_valid(self):
        self.assertTrue(IntakeForm(data=self._data()).is_valid())
    def test_severity_zero(self):
        f=IntakeForm(data=self._data(severity=0))
        self.assertFalse(f.is_valid()); self.assertIn("severity",f.errors)
    def test_severity_11(self):
        f=IntakeForm(data=self._data(severity=11))
        self.assertFalse(f.is_valid()); self.assertIn("severity",f.errors)
    def test_empty_complaint(self):
        self.assertFalse(IntakeForm(data=self._data(chief_complaint="")).is_valid())
    def test_no_consent(self):
        f=IntakeForm(data=self._data(consent=False))
        self.assertFalse(f.is_valid()); self.assertIn("consent",f.errors)
    def test_duration_zero(self):
        f=IntakeForm(data=self._data(duration_hours=0))
        self.assertFalse(f.is_valid()); self.assertIn("duration_hours",f.errors)
    def test_no_symptoms_ok(self):
        self.assertTrue(IntakeForm(data=self._data(symptoms=[])).is_valid())
    def test_severity_1(self):
        self.assertTrue(IntakeForm(data=self._data(severity=1)).is_valid())
    def test_severity_10(self):
        self.assertTrue(IntakeForm(data=self._data(severity=10)).is_valid())
EOF

# ── Dockerfile ────────────────────────────────────────────────────
cat > "$ROOT/Dockerfile" << 'EOF'
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["gunicorn","telehealth.wsgi:application","--bind","0.0.0.0:8000","--workers","2"]
EOF

# ── docker-compose.yml ────────────────────────────────────────────
cat > "$ROOT/docker-compose.yml" << 'EOF'
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: telehealth
      POSTGRES_USER: telehealth
      POSTGRES_PASSWORD: ${DB_PASSWORD:-devpassword}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL","pg_isready -U telehealth"]
      interval: 5s
      timeout: 5s
      retries: 5
  web:
    build: .
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn telehealth.wsgi:application --bind 0.0.0.0:8000"
    env_file: .env
    environment:
      DATABASE_URL: postgres://telehealth:${DB_PASSWORD:-devpassword}@db:5432/telehealth
      DJANGO_SETTINGS_MODULE: telehealth.settings.production
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app
volumes:
  pgdata:
EOF

# ── .env.example ──────────────────────────────────────────────────
cat > "$ROOT/.env.example" << 'EOF'
SECRET_KEY=change-me-to-50-random-chars
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://telehealth:devpassword@db:5432/telehealth
DB_PASSWORD=devpassword
EOF
[ -f "$ROOT/.env" ] || cp "$ROOT/.env.example" "$ROOT/.env"

# ── .github/workflows/ci.yml ──────────────────────────────────────
cat > "$ROOT/.github/workflows/ci.yml" << 'EOF'
name: CI
on:
  push:
    branches: ["**"]
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: telehealth_test
          POSTGRES_USER: telehealth
          POSTGRES_PASSWORD: testpass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5
    env:
      DJANGO_SETTINGS_MODULE: telehealth.settings.development
      DATABASE_URL: postgres://telehealth:testpass@localhost:5432/telehealth_test
      SECRET_KEY: ci-not-secret-key-for-testing-only
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r backend/requirements.txt
      - name: Run tests with coverage
        working-directory: backend
        run: |
          coverage run -m pytest --tb=short -q
          coverage report --fail-under=80
      - run: docker build -t telehealth-triage .
EOF

# ── README.md ─────────────────────────────────────────────────────
cat > "$ROOT/README.md" << 'EOF'
# TeleHealth Triage Platform

Mobile-first telehealth intake and clinician queue — Django 5 + PostgreSQL.

> **Disclaimer:** Routing suggestions only. NOT a medical diagnosis.
> Emergency? Call 911.

## Quick Start (Docker)

    cp .env.example .env   # set SECRET_KEY
    docker compose up --build
    # http://localhost:8000

## Local Dev

    cd backend
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

## Tests

    cd backend
    pytest --tb=short -q
    coverage run -m pytest && coverage report --fail-under=80

## Roles
- Patient: any authenticated user
- Clinician: is_staff=True OR member of Clinicians group

## Create Clinicians group

    cd backend
    python manage.py shell -c "
    from django.contrib.auth.models import Group
    Group.objects.get_or_create(name='Clinicians')
    "

## PWA
manifest.json configured. Add 192x192 and 512x512 PNGs to backend/static/icons/.
EOF

# ── summary ───────────────────────────────────────────────────────
echo ""
echo "=============================================="
echo "  Files written:"
echo "=============================================="
find "$ROOT" -not -path '*/.git/*' -type f | sort | sed "s|$ROOT/||"
echo "=============================================="
echo "  DONE. Now run:"
echo "    cd $ROOT"
echo "    git add -A"
echo "    git commit -m 'feat: full scaffold'"
echo "    git push origin main"
echo "=============================================="
