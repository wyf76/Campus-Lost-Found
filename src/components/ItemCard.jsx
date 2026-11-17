import { useState } from 'react';
import { formatDate } from '../data/items';

const categoryArt = {
  Electronics: 'M3 14v-2a9 9 0 0 1 18 0v2M3 14a2 2 0 0 1 2-2h1a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM16 14a2 2 0 0 1 2-2h1a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2z',
  Bags: 'M5 10a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5v9a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2zM9 5V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1M8 13h8v5H8z',
  Keys: 'M10 14a5 5 0 1 1 4-4l7 7-4 4-2-2v-2h-2zM8 9h.01',
  Clothing: 'M8 4 3 7l2 5 3-1v9h8v-9l3 1 2-5-5-3a4 4 0 0 1-8 0z',
  Books: 'M4 5h6a2 2 0 0 1 2 2v13a3 3 0 0 0-3-2H4zM20 5h-6a2 2 0 0 0-2 2v13a3 3 0 0 1 3-2h5z',
  Other: 'M9 3h6v4l2 3v9a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-9l2-3zM9 7h6M7 13h10',
};

function FlagReport({ item, onFlag, pending }) {
  const [submitted, setSubmitted] = useState(false);

  async function submit(event) {
    event.preventDefault();
    const input = event.currentTarget.elements.reason;
    const reason = input.value.trim();
    if (!reason) {
      input.setCustomValidity('Enter a reason for flagging this report.');
      input.reportValidity();
      return;
    }
    if (await onFlag(item.id, reason)) setSubmitted(true);
  }

  return (
    <details>
      <summary>Flag report</summary>
      {submitted ? <p role="status">Flag submitted for moderator review.</p> : (
        <form onSubmit={submit}>
          <label>
            Reason for flagging
            <textarea name="reason" rows={2} required maxLength={500}
              onInput={event => event.currentTarget.setCustomValidity('')} />
          </label>
          <button type="submit" className="secondary" disabled={pending}>Submit flag</button>
        </form>
      )}
    </details>
  );
}

export default function ItemCard({ item, onReturn, onEdit, onFlag, onContact, pending, children }) {
  const status = item.resolved ? 'Returned' : item.type;
  return (
    <article className="panel item-card">
      <div className="card-top">
        <span className={'category-icon ' + item.category.toLowerCase()}>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d={categoryArt[item.category]} /></svg>
        </span>
        <span className={'badge ' + status.toLowerCase()}>{status}</span>
      </div>
      <h3>{item.title}</h3>
      <p className="item-location">{item.location}</p>
      <p className="muted item-meta">{item.category} · {formatDate(item.date)}{item.pinned ? ' · Pinned' : ''}</p>
      {item.image && <img className="report-image" src={item.image} alt={item.title} loading="lazy" />}

      <details>
        <summary>View details</summary>
        {item.locationDetails && <p>{item.locationDetails}</p>}
        {item.time && <p>Time reported for item: {item.time.slice(0, 5)}</p>}
        <p className="description">{item.description}</p>
        {item.isOwn && item.contact && (
          <p>Contact: <a href={'mailto:' + item.contact}>{item.contact}</a></p>
        )}
        <p className="muted">{item.isOwn ? 'Your report' : item.author || 'Sample report'}</p>
      </details>

      {item.isOwn && !item.resolved && (onEdit || onReturn) && (
        <div className="form-actions card-actions">
          {onEdit && <button type="button" className="secondary" disabled={pending} onClick={() => onEdit(item)}>Edit</button>}
          {onReturn && <button type="button" className="secondary" disabled={pending} onClick={() => onReturn(item.id)}>
            Mark as returned
          </button>}
        </div>
      )}
      {onContact && (
        <div className="form-actions card-actions">
          <button type="button" disabled={pending} onClick={() => onContact(item.id)}>Contact poster</button>
        </div>
      )}
      {onFlag && <FlagReport item={item} onFlag={onFlag} pending={pending} />}
      {children}
    </article>
  );
}
