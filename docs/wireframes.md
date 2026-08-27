
## 2. Architecture

    Browser (Patient / Clinician)
            |  HTTPS
            v
      Gunicorn + Django 5.1
            |
       +----+----+
       |         |
    Session    CSRF
    Auth       Middleware
       |
       +--> intake/views.py
       |         |
       |    determine_triage()   <-- pure Python, no DB dependency
       |         |
       |    Intake.objects.create()
       |         |
       +--> AuditLog.objects.create()
            |
            v
      PostgreSQL 16

### Key decisions
1. Triage logic is pure Python with no Django imports — unit-testable without a DB.
2. Session auth with HttpOnly cookies — no JWT complexity for MVP.
3. Clinician access gated by is_staff OR Clinicians group — no extra user model.
4. Queue uses 30 s JS polling — acceptable substitute for WebSockets per scope.
5. WhiteNoise serves static files — no S3/CDN required for MVP.
6. Single Docker Compose file (db + web) — zero external dependencies to start.

---

## 3. Data Models

### Intake

| Field           | Type                      | Notes                                        |
|-----------------|---------------------------|----------------------------------------------|
| id              | AutoField PK              |                                              |
| patient         | FK -> User                | PROTECT — never cascade-delete               |
| chief_complaint | TextField                 | Free text, max 500 chars via form            |
| symptoms        | JSONField (list)          | Selected from controlled vocabulary          |
| severity        | PositiveSmallIntegerField | 1–10, patient-reported                       |
| duration_hours  | PositiveIntegerField      | Min 1                                        |
| red_flags       | JSONField (list)          | Detected terms from triage engine            |
| triage_level    | CharField choices         | emergency / urgent / routine / self_care     |
| triage_reason   | TextField                 | Plain-language explanation shown to patient  |
| status          | CharField choices         | new / in_review / assigned / resolved        |
| assigned_to     | FK -> User (nullable)     | SET_NULL on delete                           |
| created_at      | DateTimeField auto_add    | Indexed — descending queue order             |
| updated_at      | DateTimeField auto_now    |                                              |
| notes           | TextField blank           | Clinician internal notes                     |

### AuditLog

| Field      | Type                      | Notes                  |
|------------|---------------------------|------------------------|
| id         | AutoField PK              |                        |
| user       | FK -> User (nullable)     | SET_NULL on delete     |
| action     | CharField 100             | e.g. intake_submitted  |
| target     | CharField 200             | e.g. Intake#42         |
| ip_address | GenericIPAddressField     |                        |
| timestamp  | DateTimeField auto_add    | Indexed, descending    |
| detail     | JSONField                 | Arbitrary context dict |

---

## 4. Triage Rules (deterministic, ordered)

    Input: symptoms[], chief_complaint, severity (1-10), duration_hours

    Rule 1 — EMERGENCY
      IF any RED_FLAG_TERM in (symptoms + chief_complaint).lower()
      THEN level = "emergency"
           reason = "Call 911 or go to ER immediately"

    Rule 2 — URGENT (high severity)
      ELSE IF severity >= 8
      THEN level = "urgent"
           reason = "High severity — prompt evaluation today"

    Rule 3 — URGENT (moderate + prolonged)
      ELSE IF severity >= 6 AND duration_hours >= 24
      THEN level = "urgent"
           reason = "Moderate severity persisting > 24 h"

    Rule 4 — ROUTINE
      ELSE IF severity >= 4
      THEN level = "routine"
           reason = "Schedule a clinician appointment"

    Rule 5 — SELF_CARE (default)
      ELSE level = "self_care"
           reason = "Symptoms mild — monitor closely"

    Red flag vocabulary (partial):
      chest pain, chest pressure, shortness of breath,
      difficulty breathing, sudden severe headache, worst headache,
      loss of consciousness, fainting, stroke symptoms, facial drooping,
      arm weakness, slurred speech, coughing blood, vomiting blood,
      severe abdominal pain, suicidal, overdose

---

## 5. URL Map

| Method | URL                     | View                 | Access       |
|--------|-------------------------|----------------------|--------------|
| GET    | /accounts/login/        | Django LoginView     | Public       |
| POST   | /accounts/login/        | Django LoginView     | Public       |
| POST   | /accounts/logout/       | Django LogoutView    | Auth         |
| GET    | /intake/                | IntakeFormView       | Auth         |
| POST   | /intake/                | IntakeFormView       | Auth         |
| GET    | /intake/<pk>/           | intake_result        | Auth + owner |
| GET    | /intake/queue/          | clinician_queue      | Clinician    |
| GET    | /intake/queue/poll/     | queue_poll (JSON)    | Clinician    |
| POST   | /intake/<pk>/status/    | intake_update_status | Clinician    |
| GET    | /admin/                 | Django admin         | Staff        |

---

## 6. Wireframes

Breakpoints: 375 px mobile and 1280 px desktop.

---

### 6.1 Login — 375 px

    +----------------------------------+
    |  TeleHealth Triage               |
    +----------------------------------+
    |                                  |
    |  Log In                          |
    |                                  |
    |  Username                        |
    |  +------------------------------+|
    |  |                              ||
    |  +------------------------------+|
    |                                  |
    |  Password                        |
    |  +------------------------------+|
    |  |                              ||
    |  +------------------------------+|
    |                                  |
    |  +------------------------------+|
    |  |         Log In               ||
    |  +------------------------------+|
    |                                  |
    +----------------------------------+

---

### 6.2 Login — 1280 px

    +----------------------------------------------------------------+
    |  TeleHealth Triage                                             |
    +----------------------------------------------------------------+
    |                                                                |
    |                  +---------------------------+                 |
    |                  |  Log In                   |                 |
    |                  |                           |                 |
    |                  |  Username                 |                 |
    |                  |  +---------------------+  |                 |
    |                  |  |                     |  |                 |
    |                  |  +---------------------+  |                 |
    |                  |                           |                 |
    |                  |  Password                 |                 |
    |                  |  +---------------------+  |                 |
    |                  |  |                     |  |                 |
    |                  |  +---------------------+  |                 |
    |                  |                           |                 |
    |                  |  [       Log In        ]  |                 |
    |                  +---------------------------+                 |
    |                                                                |
    +----------------------------------------------------------------+

---

### 6.3 Patient Intake Form — 375 px

    +----------------------------------+
    |  TeleHealth Triage          [=]  |
    +----------------------------------+
    |  WARNING: ROUTING TOOL ONLY      |
    |  Not a diagnosis. Emergencies:   |
    |  CALL 911.                       |
    +----------------------------------+
    |  Complete Your Intake            |
    |                                  |
    |  Describe your main concern      |
    |  +------------------------------+|
    |  | What brings you in today?   ||
    |  |                              ||
    |  |                              ||
    |  +------------------------------+|
    |                                  |
    |  Select all symptoms that apply  |
    |  [ ] Chest pain or pressure      |
    |  [ ] Shortness of breath         |
    |  [ ] Fever                       |
    |  [ ] Cough                       |
    |  [ ] Fatigue                     |
    |  [ ] Headache                    |
    |  [ ] Nausea or vomiting          |
    |  [ ] Dizziness                   |
    |  [ ] Sore throat                 |
    |  [ ] Abdominal pain              |
    |  [ ] Rash or skin changes        |
    |  [ ] Joint or muscle pain        |
    |                                  |
    |  Overall severity (1-10)         |
    |  1 [========O========] 10   6    |
    |  (44 px tall touch target)       |
    |                                  |
    |  Symptoms duration (hours)       |
    |  +------------------------------+|
    |  |  12                          ||
    |  +------------------------------+|
    |                                  |
    |  [x] I understand this is a      |
    |      routing tool only, NOT a    |
    |      medical diagnosis. I        |
    |      consent to clinician        |
    |      review.                     |
    |                                  |
    |  +------------------------------+|
    |  |     Submit Intake  ->        ||
    |  +------------------------------+|
    |  (full-width, 48 px tall)        |
    +----------------------------------+

---

### 6.4 Patient Intake Form — 1280 px

    +----------------------------------------------------------------+
    |  TeleHealth Triage                   New Intake  |  Log Out   |
    +----------------------------------------------------------------+
    |  WARNING: Routing tool only. Not a diagnosis.                  |
    |  Emergency? Call 911 immediately.                              |
    +------------------------------------+---------------------------+
    |                                    |                           |
    |  Complete Your Intake              |  (sidebar — reserved      |
    |                                    |   for future FAQ/tips)    |
    |  Describe your main concern        |                           |
    |  +--------------------------------+|                           |
    |  | What brings you in today?     ||                           |
    |  |                                ||                           |
    |  +--------------------------------+|                           |
    |                                    |                           |
    |  Symptoms (2-column grid)          |                           |
    |  [ ] Chest pain   [ ] Fever        |                           |
    |  [ ] Shortness    [ ] Cough        |                           |
    |  [ ] Fatigue      [ ] Headache     |                           |
    |  [ ] Nausea       [ ] Dizziness    |                           |
    |  [ ] Sore throat  [ ] Abd. pain    |                           |
    |  [ ] Rash         [ ] Joint pain   |                           |
    |                                    |                           |
    |  Overall severity (1-10)           |                           |
    |  1 [=============O=======] 10  6  |                           |
    |                                    |                           |
    |  Symptoms duration (hours)  [ 12 ]|                           |
    |                                    |                           |
    |  [x] I consent...                  |                           |
    |                                    |                           |
    |  [        Submit Intake ->       ] |                           |
    +------------------------------------+---------------------------+

---

### 6.5 Triage Result — 375 px

    +----------------------------------+
    |  TeleHealth Triage          [=]  |
    +----------------------------------+
    |  Your Routing Recommendation     |
    |                                  |
    |  +------------------------------+|
    |  |  URGENT -- same-day          ||
    |  |  evaluation needed           ||
    |  +------------------------------+|
    |  (orange background badge)       |
    |                                  |
    |  Moderate-to-high severity       |
    |  persisting over 24 hours        |
    |  warrants same-day care.         |
    |                                  |
    |  WARNING: Routing suggestion     |
    |  only -- NOT a medical           |
    |  diagnosis. A clinician will     |
    |  review. If in danger, call 911. |
    |                                  |
    |  Severity reported   7/10        |
    |  Duration            36 hours    |
    |  Submitted           Aug 26 21:00|
    |                                  |
    |  [ Submit another intake ]       |
    +----------------------------------+

---

### 6.6 Triage Result — 1280 px

    +----------------------------------------------------------------+
    |  TeleHealth Triage                   New Intake  |  Log Out   |
    +----------------------------------------------------------------+
    |                                                                |
    |  Your Routing Recommendation                                   |
    |                                                                |
    |  +-----------------------------------------------------------+ |
    |  |  URGENT -- same-day evaluation needed (orange band)       | |
    |  +-----------------------------------------------------------+ |
    |                                                                |
    |  Moderate-to-high severity persisting over 24 hours           |
    |  warrants same-day care.                                       |
    |                                                                |
    |  WARNING: Routing suggestion only -- NOT a medical diagnosis.  |
    |  A clinician will review your intake.                          |
    |  If in immediate danger, call 911.                             |
    |                                                                |
    |  Severity reported   7/10                                      |
    |  Duration            36 hours                                  |
    |  Submitted           Aug 26 21:00 UTC                          |
    |                                                                |
    |  [ Submit another intake ]                                     |
    |                                                                |
    +----------------------------------------------------------------+

---

### 6.7 Clinician Queue — 375 px (card layout)

    +----------------------------------+
    |  TeleHealth Triage          [=]  |
    |  Queue  |  Log Out               |
    +----------------------------------+
    |  Intake Queue  (2 new)           |
    |                                  |
    |  [New] [In Review] [Assigned]    |
    |  [Resolved]                      |
    +----------------------------------+
    |  #          12                   |
    |  Patient    John D.              |
    |  Triage     [EMERGENCY]          |   <- red badge
    |  Severity   9/10                 |
    |  Submitted  Aug 26 20:45         |
    |  Assigned   --                   |
    |  Status     [new        v]       |
    +----------------------------------+
    |  #          11                   |
    |  Patient    Sara M.              |
    |  Triage     [urgent]             |   <- orange badge
    |  Severity   7/10                 |
    |  Submitted  Aug 26 20:32         |
    |  Assigned   --                   |
    |  Status     [new        v]       |
    +----------------------------------+
    |  <- Prev   Page 1 of 3   Next -> |
    +----------------------------------+

---

### 6.8 Clinician Queue — 1280 px (full table)

    +----+------------+-----------+------+---------------+----------+
    | #  | Patient    | Triage    | Sev  | Submitted     | Status   |
    +----+------------+-----------+------+---------------+----------+
    | 12 | John D.    |[EMERGENCY]| 9/10 | Aug 26 20:45  | [new  v] |  <- red row
    | 11 | Sara M.    |[urgent]   | 7/10 | Aug 26 20:32  | [new  v] |  <- orange row
    | 10 | Carlos R.  |[routine]  | 5/10 | Aug 26 19:15  | [new  v] |
    |  9 | Priya K.   |[self-care]| 2/10 | Aug 26 18:50  | [new  v] |
    +----+------------+-----------+------+---------------+----------+
    |  <- Prev    Page 1 of 3    Next ->                             |
    +----------------------------------------------------------------+

    Status dropdown options per row:
      New / In Review / Assigned / Resolved
      Selecting any option auto-submits (onchange)
      Selecting "Assigned" sets assigned_to = current clinician

---

## 7. Security Controls

| Control               | Implementation                                       |
|-----------------------|------------------------------------------------------|
| Authentication        | django.contrib.auth session-based login              |
| Session expiry        | SESSION_COOKIE_AGE = 3600 (1 hour)                   |
| Session hardening     | SESSION_COOKIE_HTTPONLY = True                       |
| CSRF protection       | CsrfViewMiddleware + csrf_token on all POST forms    |
| Role-based access     | is_clinician() guard on all queue views              |
| Audit logging         | AuditLog row on every intake + every status change   |
| HTTPS (production)    | SECURE_SSL_REDIRECT = True                           |
| Secure cookies (prod) | SESSION_COOKIE_SECURE + CSRF_COOKIE_SECURE = True    |
| HSTS (production)     | SECURE_HSTS_SECONDS = 31536000                       |
| Clickjacking          | XFrameOptionsMiddleware (DENY)                       |
| Password validation   | Django built-in validators                           |
| Medical disclaimer    | Shown on form page, result page, and every response  |

---

## 8. CI/CD Pipeline

    git push
       |
       v
    GitHub Actions: .github/workflows/ci.yml
       |
       +-- Start postgres:16-alpine service container
       +-- pip install -r backend/requirements.txt
       +-- coverage run -m pytest --tb=short -q
       +-- coverage report --fail-under=80
       +-- docker build -t telehealth-truage .
       |
       v
    Pass = green check on commit
    Fail = blocked PR merge (enable branch protection on main)

---

## 9. PWA Configuration

    File: backend/static/manifest.json
    - name: "TeleHealth Triage"
    - short_name: "Triage"
    - start_url: "/"
    - display: "standalone"
    - theme_color: "#0077cc"
    - background_color: "#f5f7fa"
    - icons: 192x192 and 512x512 PNG in backend/static/icons/

    Add to base.html:
      <link rel="manifest" href="/static/manifest.json" />
      <meta name="theme-color" content="#0077cc" />

    Service worker: not in MVP scope. Add Workbox for offline support.

---

## 10. Setup Cheatsheet

    # 1. Clone and configure
    git clone https://github.com/SACS-MMC-JMHT/telehealth-triage.git
    cd telehealth-triage
    cp .env.example .env          # set SECRET_KEY and DB_PASSWORD

    # 2. Docker (recommended)
    docker compose up --build
    # App:   http://localhost:8000
    # Admin: http://localhost:8000/admin/

    # 3. Local dev (no Docker)
    cd backend
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

    # 4. Tests
    cd backend
    pytest --tb=short -q
    coverage run -m pytest && coverage report --fail-under=80

    # 5. Create Clinicians group (one-time)
    python manage.py shell -c "
    from django.contrib.auth.models import Group
    Group.objects.get_or_create(name='Clinicians')
    "
    # Then assign clinician users to the group via /admin/auth/user/
