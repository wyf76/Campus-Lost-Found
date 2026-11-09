# Campus Lost & Found

Lab 7 prototype for Santa Clara University, built with React and Vite and connected to the team's Django report and account APIs.

## Run the demo

From the repository folder, run:

```sh
npm ci
npm run dev
```

Open the local URL printed by Vite. The demo opens with six fictional reports and needs only Node.js and npm. Practice reports stay in the current browser.

### Quick walkthrough

1. Search for **keys**, switch to **Found**, and open **View details**.
2. Clear the search and choose **Report an item** to post a fictional report.
3. Open **My reports** and choose **Mark as returned**. The report stays in your history and leaves the open board.
4. Refresh to see that the practice report is still in your browser.

## Use the shared campus board

1. Follow [BACKEND_SETUP.md](BACKEND_SETUP.md) to set up PostgreSQL, install the Python dependencies, and migrate the database.
2. Run Django at `127.0.0.1:8000` in a second terminal. Keep Vite running and open the frontend from its local URL.
3. Choose **SCU sign in**. For a new account, use **Create an account**, then **Send code** and **Verify email**. In local console email mode, the verification code appears in the Django terminal.
4. Sign in to browse shared open reports. Post a report, find it under **My reports**, edit it while it is open, and mark it as returned.

Vite forwards `/api` and `/media` to Django. The campus board uses Django sessions and CSRF protection. Demo reports and shared reports are separate. Chat, saved reports, notifications, password reset, and moderation are available in the backend API and are outside this frontend milestone.

Use `npm run build` to create the frontend bundle in `dist/`.
