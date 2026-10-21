import { formatDate } from '../data/items';

export default function ItemCard({ item, onReturn }) {
  return (
    <article className="panel item-card">
      <span className="badge">{item.resolved ? 'Returned' : item.type}</span>
      <h3>{item.title}</h3>
      <p>{item.location}</p>
      <p className="muted">{item.category} · {formatDate(item.date)}</p>

      {/* The browser handles expanding and closing the details. */}
      <details>
        <summary>View details</summary>
        <p className="description">{item.description}</p>
        {item.isOwn && (
          <p>
            Contact: <a href={`mailto:${item.contact}`}>{item.contact}</a>
          </p>
        )}
      </details>

      <p className="muted">{item.isOwn ? 'Your report' : 'Sample report'}</p>
      {item.isOwn && !item.resolved && (
        <button type="button" className="secondary" onClick={() => onReturn(item.id)}>
          Mark as returned
        </button>
      )}
    </article>
  );
}
