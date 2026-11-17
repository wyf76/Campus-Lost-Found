# Test the Lab 8 MVP on two laptops

Use one laptop to host Campus Lost & Found and post a report. Use the second laptop to find the report and send a private message. Both accounts use the same campus board.

## 1. Start the app on laptop A

1. Connect both laptops to the same Wi-Fi. Laptop A needs the project and its dependencies. Laptop B only needs a browser.
2. On laptop A, complete the [backend setup](BACKEND_SETUP.md) to start PostgreSQL, configure `.env.backend`, and apply the migrations.
3. Find laptop A’s Wi-Fi IPv4 address in its network settings. On a Mac, `ipconfig getifaddr en0` usually prints it. If the address is `192.168.1.167`, add this line to the project’s local `.env.backend`:

   ```dotenv
   CAMPUS_ALLOWED_HOSTS=192.168.1.167
   ```

   If the setting already has entries, add the IP to the comma-separated list.

4. From the repository root, activate the Python environment and start Django. If it was already running, restart it so it picks up the setting.

   ```sh
   python manage.py runserver 127.0.0.1:8000
   ```

5. Open a second terminal in the repository root. Use laptop A’s actual Wi-Fi address in the Vite command.

   ```sh
   npm ci
   npm run dev -- --host 192.168.1.167 --strictPort
   ```

6. On **both laptops**, open the same URL in a browser. Replace the example IP with laptop A’s address and keep `http://` at the beginning.

   ```text
   http://192.168.1.167:4173/?board=campus
   ```

Keep laptop A awake with both servers running. If laptop B times out, try a shared phone hotspot and repeat the IP configuration using laptop A’s new address.

## 2. Sign in with two student accounts

Sign in as the **report author** on laptop A and a different student, the **finder**, on laptop B. If you need accounts, use **Create an account** on each screen with a different `@scu.edu` address. Click **Send code**, enter the six-digit verification code, and sign in. In console email mode, both codes appear in the Django terminal on laptop A.

For a one-laptop test, open the same campus board URL in a regular window and a private window and use a different account in each.

## 3. Test messaging and mark the item returned

| Device | What to do | Expected result |
| --- | --- | --- |
| Laptop A · Author | Click **Report an item**. Post a lost backpack at Learning Commons with a photo. | The report and photo appear in **My reports**. |
| Laptop B · Finder | Reload the campus board, open **Lost**, and search for “backpack.” Click **Contact poster** on the new report. Send “I found your backpack. Can we meet at the library entrance?” | The report appears on laptop B, and the message appears in the conversation. |
| Laptop A · Author | Open **Messages**, click **Refresh messages**, and select the backpack conversation. Reply with a pickup time. | The finder’s message is visible and the reply appears below it. |
| Laptop B · Finder | Click **Refresh messages**. | The author’s reply appears in the same conversation. |
| Laptop A · Author | Click **Campus board**, open **My reports**, and click **Mark as returned**. | The report appears in **Returned**. |
| Laptop B · Finder | Click **Refresh messages** in the conversation. | Both messages are still visible and the conversation is read-only. |

## Show what changed since the first prototype

For the Lab 8 recording, briefly show the sample board and form from the first frontend commit (`8b8c4ca`). It stored practice reports in a single browser. Then show the test above with shared accounts, a shared photo, and a two-way message exchange.

To run the first frontend alongside the MVP, open another terminal in the repository root:

```sh
git worktree add --detach ../Campus-Lost-Found-prototype 8b8c4ca
cd ../Campus-Lost-Found-prototype
npm ci
npm run dev -- --host 127.0.0.1 --port 4174 --strictPort
```

Open the [first prototype](http://127.0.0.1:4174/) on laptop A.
