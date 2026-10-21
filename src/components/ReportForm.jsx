import { categories } from '../data/items';

export default function ReportForm({ onSubmit, onCancel }) {
  const today = new Date().toLocaleDateString('en-CA');

  function handleSubmit(event) {
    // Read inputs by their name attributes without reloading the page.
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));

    // HTML required checks empty fields; also reject text containing only spaces.
    for (const field of ['title', 'location', 'description']) {
      values[field] = values[field].trim();
      if (!values[field]) {
        form.elements[field].setCustomValidity('Please enter more than spaces.');
        form.elements[field].reportValidity();
        return;
      }
    }

    // App owns the report list and browser storage; the form only sends data.
    // isOwn identifies browser-local reports, not an authenticated user.
    onSubmit({
      ...values,
      id: globalThis.crypto?.randomUUID?.() || `report-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      isOwn: true,
      resolved: false,
    });
  }

  return (
    <form onSubmit={handleSubmit} onInput={event => event.target.setCustomValidity('')}>
      <p className="muted">Reports are saved only in this browser.</p>
      <label>
        Status
        <select name="type" defaultValue="Lost">
          <option>Lost</option>
          <option>Found</option>
        </select>
      </label>
      <label>
        Item name
        <input name="title" placeholder="e.g. Black backpack" required maxLength={80} />
      </label>
      <label>
        Category
        <select name="category">
          {categories.map(value => <option key={value}>{value}</option>)}
        </select>
      </label>
      <label>
        Date lost or found
        <input type="date" name="date" defaultValue={today} max={today} required />
      </label>
      <label>
        Campus location
        <input name="location" placeholder="e.g. Learning Commons" required maxLength={100} />
      </label>
      <label>
        Description
        <textarea name="description" rows={3} required maxLength={600} />
      </label>
      <label>
        Contact email
        <input type="email" name="contact" placeholder="you@example.edu" required maxLength={160} />
      </label>
      <div className="form-actions">
        <button type="submit">Save report</button>
        <button type="button" className="secondary" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}
