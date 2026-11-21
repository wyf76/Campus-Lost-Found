# Two-Laptop MVP Test

## Purpose

Verify that two different SCU users can use the deployed campus board to share and update a lost-and-found report. This test must use the deployed site and the **Campus board**, not the demo board, because demo reports are stored only in one browser.

## Current status

**Blocked until the Render deployment is live.** The deployment log reports exit status `127`. The deployed commit (`7af360f`) does not include `gunicorn` in `requirements.txt`, while the current local working tree does. If Render's Start Command is `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`, add Gunicorn to the branch Render deploys and redeploy. Check the final log line for the exact missing command.

The shown Render build command only installs Python dependencies; it does not run `npm ci` or `npm run build`. If this is the only Render service, the React frontend is not being deployed. Before the TA test, deploy the frontend and make sure its `/api` requests reach this Django service on the same public site origin (or configure a deliberate production API proxy).

The deployed `main` settings read `CAMPUS_DJANGO_SECRET_KEY`, `CAMPUS_DB_NAME`, `CAMPUS_DB_USER`, `CAMPUS_DB_PASSWORD`, `CAMPUS_DB_HOST`, and `CAMPUS_DB_PORT`; they also append `CAMPUS_ALLOWED_HOSTS` to Django's allowed hosts. The `.env.backend` file is local-only, so these values must be configured in Render. The local working-tree change that reads Neon `DATABASE_URL` is not in commit `7af360f`.

## Test setup

- Two laptops with internet access and separate browser sessions.
- The same public Render URL on both laptops, opened with `?board=campus`.
- Two different, active, email-verified `@scu.edu` accounts: **User A** and **User B**.
- Render configured to use the same Neon PostgreSQL production database for both requests.
- Use fictional report details only. Do not include real contact information or sensitive item details.

If email verification is not configured for delivery, prepare the two verified accounts before the TA session. Do not rely on the local demo board for this test.

## Test procedure

| Step | Laptop / account | Action | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Both laptops | Open the deployed URL with `?board=campus`. | Both show the campus board and the sign-in flow. | Screenshot from each laptop, with account details hidden. |
| 2 | Laptop A / User A | Sign in and post a synthetic lost-item report. Use a unique title such as `TA-MVP-<date-time>-A`. | The success message appears; the report is visible in **My reports**. | Screenshot of the submitted report and success message. |
| 3 | Laptop B / User B | Sign in, refresh the campus board, then search for the unique title. | User B can find the same report, demonstrating that it came from the shared backend rather than Laptop A's browser storage. | Screenshot showing the matching report. |
| 4 | Laptop B / User B | Open the report details and verify its type, title, category, date, location, and description. | The details match what User A submitted. | Screenshot of the details. |
| 5 | Laptop A / User A | Open **My reports** and mark the report as returned/resolved. | The UI confirms the update; the report remains in User A's history. | Screenshot of the resolved report in **My reports**. |
| 6 | Laptop B / User B | Refresh the open campus board and search for the same title. | The resolved report no longer appears among open reports. | Screenshot of the refreshed results. |

## Pass criteria

- Both accounts can sign in from separate laptops.
- A report created on Laptop A appears on Laptop B after refresh.
- User B can inspect the same report details.
- User A can resolve the report, and Laptop B no longer shows it as open.
- Refreshing or closing either browser does not remove the shared report or its resolved status.

## Results record

| Field | Result |
| --- | --- |
| Test date / time | Not run yet |
| Deployed URL / commit | Fill in after Render deployment succeeds |
| Laptop A / browser | Fill in during test |
| Laptop B / browser | Fill in during test |
| Overall result | Blocked by Render deployment failure |
| Issues / evidence links | Fill in during test |

## Scope notes

- The local **Demo board** stores practice reports in that browser and is not evidence of cross-laptop sharing.
- Chat, saved reports, notifications, moderation, and image upload are not part of this MVP test because the current frontend milestone does not expose those backend features as a complete user flow.
- After the test, keep the synthetic report marked resolved and record its title so it can be identified later.
