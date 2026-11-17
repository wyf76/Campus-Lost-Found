# Campus Lost & Found

Campus lost and found MVP for Santa Clara University, built with React, Vite, and Django.

[Lab 8 TA guide for testing on two laptops](TA_DEMO.md)

## Run the demo

Open a terminal in the repository root and run:

```sh
npm ci
npm run dev -- --host 127.0.0.1
```

Open the local URL printed by Vite, usually `http://127.0.0.1:4173/`. The demo opens with six fictional reports and needs only Node.js and npm. Practice reports stay in the current browser.

### Quick walkthrough

1. Search for **keys**, switch to **Found**, and open **View details**.
2. Clear the search and choose **Report an item** to post a fictional report.
3. Open **My reports** and choose **Mark as returned**. The report stays in your history and leaves the open board.
4. Refresh to see that the practice report is still in your browser.

## Set up the shared campus board

1. Follow [BACKEND_SETUP.md](BACKEND_SETUP.md) to set up PostgreSQL, install the Python dependencies, and run the migrations.
2. Keep Vite running. In a second terminal at the project root, activate the Python environment from the backend guide and run:

   ```sh
   python manage.py runserver 127.0.0.1:8000
   ```

3. Open the Vite URL and choose **SCU sign in**. For a new account, choose **Create an account** with your `@scu.edu` email, then **Send code** and **Verify email**. In console email mode, copy the verification code from the Django terminal.

Vite forwards `/api` and `/media` to Django. The campus board uses Django sessions and CSRF protection. Demo reports and shared reports are separate.

Signed-in users can flag another user's report. Verified moderator accounts have a **Moderation** button for reviewing flags, browsing report history and statistics, pinning reports, marking reports as returned, and blocking eligible student accounts. Moderators can restore access from **Blocked students**. Escalating a flag to university staff requires SMTP and a configured moderation inbox. See [BACKEND_SETUP.md](BACKEND_SETUP.md) for email settings.

Choose **Contact poster** on another student's open report to start a private conversation. Open **Messages** to read and reply, and use **Refresh messages** to check for replies. Conversations remain readable after an item is marked returned.

Saved reports, in-app notifications, and password reset are available in the backend API.

Use `npm run build` to create the frontend bundle in `dist/`.
