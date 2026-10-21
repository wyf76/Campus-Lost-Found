# Campus Lost & Found

A simple class project built with React, Vite, and plain CSS.

## Run the project

```bash
npm install
npm run dev
```

Open the local URL printed in the terminal. Use `npm run build` to create a production build in `dist/`.

## Where to make changes

| File | Purpose |
| --- | --- |
| `src/App.jsx` | Main page, search, filters, and saved reports |
| `src/components/ItemCard.jsx` | A plain item card with expandable details |
| `src/components/ReportForm.jsx` | The form for reporting a lost or found item |
| `src/data/items.js` | Sample items, categories, and date formatting |
| `src/styles.css` | Page layout, colors, and mobile styles |
| `src/main.jsx` | Starts the React app |

## How it works

1. `App.jsx` combines sample items with reports saved in this browser.
2. Search and dropdowns filter which items appear.
3. Each `ItemCard` uses HTML `<details>` to show more information.
4. The report button shows `ReportForm` directly on the page.
5. Submitting the form adds a report and switches to My reports.
6. Your reports can be marked as returned. Returned items remain in My reports.

React state tracks the reports, filters, and whether the form is open. The form uses native HTML inputs and validation. An effect saves reports to `localStorage` whenever they change.

To change the appearance, start with `styles.css`. To add sample items or categories, edit `data/items.js`. To change the page layout, edit the JSX returned by `App.jsx`.

This is a student prototype with fictional sample items. Reports stay in the current browser; there is no shared database or login. Reports saved with the earlier frontend still work. A real shared service would need a backend and user accounts.
