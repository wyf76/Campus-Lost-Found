import { categories } from '../data/items';

const locations = {
  learning_commons: 'Learning Commons',
  benson_center: 'Benson Center',
  scdi: 'SCDI',
  bergin_hall: 'Bergin Hall',
  heafey_hall: 'Heafey Hall',
  alumni_science_hall: 'Alumni Science Hall',
  daly_science_center: 'Daly Science Center',
  oconnor_hall: "O'Connor Hall",
  kenna_hall: 'Kenna Hall',
  vari_hall: 'Vari Hall',
  lucas_hall: 'Lucas Hall',
  loyola_hall: 'Loyola Hall',
  alameda_hall: 'Alameda Hall',
  dowd_art_building: 'Edward M. Dowd Art and Art History Building',
  malley_center: 'Malley Center',
  orradre_library: 'Orradre Library',
  other: 'Other',
};

export default function ReportForm({ onSubmit, onCancel, campus, editing, pending }) {
  const today = new Date().toLocaleDateString('en-CA');

  function handleSubmit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    const textFields = campus ? ['title', 'description'] : ['title', 'location', 'description'];

    for (const field of textFields) {
      values[field] = values[field].trim();
      if (!values[field]) {
        form.elements[field].setCustomValidity('Please enter more than spaces.');
        form.elements[field].reportValidity();
        return;
      }
    }

    if (campus) {
      const { type, category, date, ...details } = values;
      const body = { ...details, category: category.toLowerCase(), happened_on: date };
      if (!editing) body.item_type = type.toLowerCase();
      onSubmit(body);
      return;
    }

    onSubmit({
      ...values,
      id: globalThis.crypto?.randomUUID?.() || 'report-' + Date.now() + '-' + Math.random().toString(36).slice(2),
      isOwn: true,
      resolved: false,
    });
  }

  return (
    <form onSubmit={handleSubmit} onInput={event => event.target.setCustomValidity('')}>
      <fieldset disabled={pending}>
        <p className="muted">{campus ? 'Shared with signed-in SCU users.' : 'Practice report saved in this browser.'}</p>
        <div className="form-grid">
          <label>
            Report type
            <select name="type" defaultValue={editing?.type || 'Lost'} disabled={Boolean(editing)}>
              <option>Lost</option>
              <option>Found</option>
            </select>
          </label>
          <label>
            Category
            <select name="category" defaultValue={editing?.category}>
              {categories.map(value => <option key={value}>{value}</option>)}
            </select>
          </label>
          <label>
            Item name
            <input name="title" placeholder="e.g. Black backpack" defaultValue={editing?.title} required maxLength={campus ? 100 : 80} />
          </label>
          <label>
            Date lost or found
            <input type="date" name="date" defaultValue={editing?.date || today} max={editing?.date > today ? editing.date : today} required />
          </label>
          <label>
            Campus location
            {campus ? (
              <select name="location" defaultValue={editing?.locationCode || ''} required>
                <option value="" disabled>Select a location</option>
                {Object.entries(locations).map(([code, label]) => <option key={code} value={code}>{label}</option>)}
              </select>
            ) : (
              <input name="location" placeholder="e.g. Learning Commons" required maxLength={100} />
            )}
          </label>
          {campus ? (
            <label>
              Location details (optional)
              <input name="location_details" defaultValue={editing?.locationDetails}
                placeholder="e.g. Study tables by the entrance" maxLength={200} />
            </label>
          ) : (
            <label>
              Contact email
              <input type="email" name="contact" placeholder="you@example.edu" required maxLength={160} />
            </label>
          )}
        </div>
        <label>
          Description
          <textarea name="description" rows={3} defaultValue={editing?.description}
            placeholder="Include a few details that would help identify the item." required maxLength={campus ? undefined : 600} />
        </label>
        <div className="form-actions">
          <button type="submit">{pending ? 'Saving…' : editing ? 'Save changes' : 'Post report'}</button>
          <button type="button" className="secondary" onClick={onCancel}>Cancel</button>
        </div>
      </fieldset>
    </form>
  );
}
