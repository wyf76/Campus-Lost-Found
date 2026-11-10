# Campus Lost & Found

Lab 7 prototype for Santa Clara University, built with React and Vite and connected to the team's Django report and account APIs.

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

Vite forwards `/api` and `/media` to Django. The campus board uses Django sessions and CSRF protection. Demo reports and shared reports are separate. Chat, saved reports, notifications, password reset, and moderation are available in the backend API and are outside this frontend milestone.

Use `npm run build` to create the frontend bundle in `dist/`.
