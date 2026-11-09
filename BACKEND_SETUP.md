# Campus Lost and Found — Backend Setup

## Current scope

The Django backend provides verified SCU accounts, password reset, read-only
profiles, lost and found reports, report search and history, private chat,
notifications, saved reports, and moderator tools. PostgreSQL stores the data.

The React frontend connects to account verification, sign-in, and the core report flow. See [README.md](README.md) to run the demo or shared campus board.

## Requirements

The backend has been tested with Python 3.13 and PostgreSQL 17.
Python dependencies are pinned in requirements.txt.

These settings are for local development.

## 1. Create a Python environment

From the repository root:

```bash
python3 -m venv .venv-local
source .venv-local/bin/activate
python -m pip install -r requirements.txt
```

On Windows, activate with:

```powershell
.venv-local\Scripts\Activate.ps1
```

## 2. Start PostgreSQL and create a local database

Each developer should use their own local database password.

For macOS with Postgres.app 17:

```bash
export PATH="/Applications/Postgres.app/Contents/Versions/17/bin:$PATH"
```

With PostgreSQL running, execute these commands using a database
administrator account:

```bash
createuser --createdb --no-superuser --no-createrole --pwprompt campus_app
createdb --owner=campus_app campus_lost_found
```

The CREATEDB permission is for local development so Django can create
its separate test database. The application role is not a superuser.

If the role or database already exists, inspect the existing setup
instead of deleting it.

## 3. Configure the backend

On first setup, copy the example file:

```bash
cp -n .env.backend.example .env.backend
```

Populate your database password and generate your own Django secret key:

```bash
python - <<'PY'
from getpass import getpass
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from dotenv import dotenv_values, set_key

path = Path(".env.backend")
values = dotenv_values(path, interpolate=False)

password = getpass("Your local campus_app database password: ")

if not password:
    raise SystemExit("A database password is required.")

set_key(str(path), "CAMPUS_DB_PASSWORD", password)

if not values.get("CAMPUS_DJANGO_SECRET_KEY"):
    set_key(
        str(path),
        "CAMPUS_DJANGO_SECRET_KEY",
        get_random_secret_key(),
    )

path.chmod(0o600)
print("Local configuration saved.")
PY
```

The example uses:
- Database: campus_lost_found
- Database login: campus_app
- Host: 127.0.0.1
- Port: 5432

Change these values in .env.backend if your local setup differs.
127.0.0.1 refers to your own computer, not another teammate's database.

Never commit .env.backend or share another developer's secret key.

## 4. Apply migrations and run checks

```bash
python manage.py check
python manage.py migrate
python manage.py test
python manage.py runserver
```

Keep the existing migration files. Apply them to your new database;
do not regenerate or delete them to set up a fresh checkout.

## Email modes

### Console — default for development

```text
CAMPUS_EMAIL_BACKEND=console
```

Emails, including verification and reset codes, appear in the
development server's Terminal output. No Gmail password is required.

### SMTP — real delivery

```text
CAMPUS_EMAIL_BACKEND=smtp
CAMPUS_EMAIL_USER=your-authorized-sender@gmail.com
CAMPUS_EMAIL_PASSWORD=your-app-password
```

Use an authorized sender and its Gmail app password, not its normal
Google account password. Store credentials only in local configuration
or the deployment environment.

Sender addresses can be Gmail addresses. Platform registration and
code-request recipients must still use the exact scu.edu domain.

The automated email tests use an in-memory backend and do not send
real messages.

For Python.org installations on macOS, a certificate verification error
may require completing Python's certificate installation:

```bash
open "/Applications/Python 3.13/Install Certificates.command"
```

## API endpoints

| Method | Path | JSON fields |
|---|---|---|
| GET | /api/auth/csrf/ | None |
| POST | /api/auth/register/ | full_name, email, password |
| POST | /api/auth/verification/request/ | email |
| POST | /api/auth/verification/confirm/ | email, code |
| POST | /api/auth/login/ | email, password |
| POST | /api/auth/logout/ | None required |
| GET | /api/users/me/ | None |
| GET | /api/users/{user_id}/ | None |
| POST | /api/auth/password-reset/request/ | email |
| POST | /api/auth/password-reset/confirm/ | email, code, new_password |

JSON field values must be strings. Codes must be six-digit strings,
including any leading zeros.

For POST requests:
1. Request /api/auth/csrf/.
2. Preserve the returned cookies.
3. Send the csrfToken value in the X-CSRFToken header.
4. Send JSON with Content-Type: application/json.

Login rotates the CSRF token. Use the new csrfToken from the login
response for subsequent POST requests.

Preserve the session cookie across requests. Sessions expire after
eight hours unless ended or invalidated earlier.

New registrations are inactive and unverified. Request a verification
code and confirm it before attempting login.

Verification and reset codes expire after ten minutes. Each code allows
five attempts. Sending has a sixty-second cooldown and a limit of five
emails per account per one-hour window, tracked separately for each
purpose.

Password reset does not log the user in or unblock an inactive account.

## Profile and role rules

Public profiles expose only:
- id
- full_name
- email
- profile_picture

The current-user and login responses also include is_moderator for the
authenticated user's navigation.

Profile endpoints reject edits. Password changes use the reset flow.

The `is_moderator` field identifies the platform moderator role.
Moderator endpoints enforce this role on the server.

## Report, chat, and moderation API

These endpoints require an active, verified session. Send the session cookie
and the current `X-CSRFToken` header with POST, PATCH, and DELETE requests.
Send `Content-Type: application/json` for JSON bodies. Report creation also
accepts multipart form data for an optional image.

| Method | Path | Purpose |
|---|---|---|
| GET, POST | /api/reports/ | Search or create reports |
| GET | /api/reports/{id}/ | View a report |
| PATCH | /api/reports/{id}/edit/ | Edit your own open report |
| POST | /api/reports/{id}/resolve/ | Resolve a report as its author or a moderator |
| GET | /api/users/me/reports/ | View your report history |
| GET | /api/reports/saved/ | View your private saved reports |
| POST, DELETE | /api/reports/{id}/save/ | Save or unsave a report |
| POST | /api/reports/{id}/conversations/ | Open a conversation with the report author |
| GET | /api/conversations/ | List your conversations |
| GET, POST | /api/conversations/{id}/messages/ | Read or send messages |
| GET | /api/notifications/ | List up to 50 unread message notifications |
| POST | /api/notifications/{id}/read/ | Mark a notification as read |
| POST | /api/reports/{id}/flag/ | Flag a report with a JSON reason |
| GET | /api/reports/flags/ | List flags as a moderator |
| POST | /api/reports/flags/{flag_id}/escalate/ | Escalate a flag as a moderator |
| POST, DELETE | /api/reports/{id}/pin/ | Pin or unpin a report as a moderator |
| GET | /api/moderation/reports/ | View platform-wide report history as a moderator |
| GET | /api/moderation/statistics/ | View aggregate counts as a moderator |
| POST | /api/users/{user_id}/block/ | Block an eligible student as a moderator |

- Report creation takes `item_type`, `title`, `category`, `happened_on`,
  `location`, and `description`. The server sets the author from the session.
  `location_details`, `happened_time`, and the multipart `image` are optional.
- Report search supports `q`, `type`, `category`, `location`, `date_from`,
  `date_to`, `status`, and `sort`. The student feed defaults to open reports
  with pinned reports first. An explicit `sort=newest` or `sort=oldest` uses
  chronological order. Moderator history defaults to all report statuses.
- Send `happened_time` as a 24-hour string such as `14:30`. The API returns
  a time such as `14:30:00` or `null`. On edit, omit it to keep the stored
  value or send an empty string to clear it.
- Send chat messages as JSON with a `body` string. Existing conversations
  remain readable after resolution. New messages require an open report.
- Escalation requires SMTP and a confirmed university staff inbox set in
  `CAMPUS_MODERATION_EMAIL`. Leave this blank for local setup and testing.

## Frontend integration

Use a same-origin setup or development proxy for browser API calls. Preserve
cookies across requests and refresh the CSRF token from the login response.
The default report feed requires login. Use Django as the source of truth for
reports and account state when connecting the React frontend.

Share `.env.backend.example` with the team. Each developer should configure
their own `.env.backend`, local database credentials, and Django secret key.
Console email mode is sufficient for local verification and password resets.
