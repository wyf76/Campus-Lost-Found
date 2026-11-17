# Lab 8 MVP demo

Campus Lost & Found lets SCU students post and find lost or found items, arrange a pickup privately, and mark an item as returned.

## Before the demo

1. Start PostgreSQL, Django, and Vite using the [shared campus board setup](README.md#set-up-the-shared-campus-board). Open the [local campus board](http://127.0.0.1:4173/?board=campus).
2. Prepare two verified student accounts. In local console email mode, use **Create an account**, **Send code**, and **Verify email** for each account. The six-digit codes appear in the Django terminal. Have a sample photo ready to upload.
3. Sign in as the report author in a regular browser window and as the finder in a private window. For two laptops, connect both to the same Wi-Fi, add the host laptop’s Wi-Fi IP to `CAMPUS_ALLOWED_HOSTS` in its local `.env.backend`, and restart Django. Start Vite on that address with `npm run dev -- --host <host-ip> --strictPort`. Open `http://<host-ip>:4173/?board=campus` on both laptops.

## Show the first prototype

The first frontend is at commit `8b8c4ca`. To run it alongside the MVP, open a separate terminal in the repository and run:

```sh
git worktree add --detach ../Campus-Lost-Found-prototype 8b8c4ca
cd ../Campus-Lost-Found-prototype
npm ci
npm run dev -- --host 127.0.0.1 --port 4174 --strictPort
```

Open [the original prototype](http://127.0.0.1:4174/). Briefly show the sample board and report form. The prototype stored practice reports in one browser. In the MVP, verified students share reports through Django, upload photos, message each other, and browse returned items.

## Walk through one return

1. **Author** — Click **Report an item**. Post a lost backpack at Learning Commons with a photo. In **My reports**, use **Edit** to add an identifying detail.
2. **Finder** — Open **Lost**, search for “backpack,” and show the author’s report and photo. Click **Contact poster** and send “I found your backpack. Can we meet at the library entrance?”
3. **Author** — Open **Messages**, click **Refresh messages**, and select the backpack conversation. Reply with a pickup time. On the finder’s screen, refresh messages to show the reply.
4. **Author** — Go back to the campus board, open **My reports**, and click **Mark as returned**. Show the backpack in **Returned**. On the finder’s screen, refresh and show that it has left **Lost**.
5. **Finder** — Open the conversation again. Show that both messages are still available and the conversation is read-only.

If there’s time, show a student flagging a separate practice report and a verified moderator reviewing the flag and pinning or unpinning the report in **Moderation**.

For the Lab 8 upload, record the prototype comparison and this walkthrough. End by showing the MVP commit on GitHub’s `main` branch.
