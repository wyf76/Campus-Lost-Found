import { useEffect, useState } from 'react';
import ItemCard from './components/ItemCard';
import ReportForm from './components/ReportForm';
import { categories, sampleItems } from './data/items';

const STORAGE_KEY = 'campus-lost-found-reports-v1';

// Keep this key stable so saved reports survive frontend changes.
// Invalid or unreadable browser data falls back to an empty list.
function loadReports() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    if (!Array.isArray(saved)) return [];

    // Check saved fields before using them in searches and date formatting.
    return saved.filter(item => {
      if (!item || !item.isOwn || typeof item.id !== 'string') return false;
      const hasText = ['title', 'location', 'description', 'contact'].every(
        field => typeof item[field] === 'string'
      );
      const validDate = /^\d{4}-\d{2}-\d{2}$/.test(item.date)
        && !Number.isNaN(new Date(item.date).getTime());

      return hasText && validDate && categories.includes(item.category)
        && ['Lost', 'Found'].includes(item.type);
    });
  } catch {
    return [];
  }
}

export default function App() {
  const [reports, setReports] = useState(loadReports);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('All items');
  const [category, setCategory] = useState('All categories');
  const [showForm, setShowForm] = useState(false);
  const [message, setMessage] = useState('');
  const [storageError, setStorageError] = useState(false);

  // Save whenever a report is added or marked as returned.
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(reports));
      setStorageError(false);
    } catch {
      setStorageError(true);
    }
  }, [reports]);

  const items = [...reports, ...sampleItems];
  const visibleItems = items.filter(item => {
    // Returned items stay in My reports but leave the main board.
    const matchesStatus = filter === 'My reports'
      ? item.isOwn
      : !item.resolved && (filter === 'All items' || item.type === filter);
    const matchesCategory = category === 'All categories' || item.category === category;
    const text = `${item.title} ${item.location} ${item.description}`.toLowerCase();
    return matchesStatus && matchesCategory && text.includes(query.trim().toLowerCase());
  });

  function addReport(item) {
    setReports(current => [item, ...current]);
    setShowForm(false);
    // Clear old filters so the newly saved report is immediately visible.
    setFilter('My reports');
    setQuery('');
    setCategory('All categories');
    setMessage('Report added. You can find it under My reports.');
  }

  function markReturned(id) {
    // Create an updated array so React rerenders and the save effect runs.
    setReports(current => current.map(item => (
      item.id === id ? { ...item, resolved: true } : item
    )));
    setMessage('Item marked as returned. It is still listed under My reports.');
  }

  return (
    <main className="container">
      <header>
        <p className="muted">Santa Clara University · Student project</p>
        <h1>Campus Lost & Found</h1>
        <p>Look for a lost item or report something you found on campus.</p>
        <button
          type="button"
          aria-expanded={showForm}
          aria-controls="report-section"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? 'Close report form' : 'Report an item'}
        </button>
      </header>

      <p className="message" role="status">{message}</p>
      {storageError && (
        <p role="alert">Browser storage is unavailable. New changes will be lost after a refresh.</p>
      )}

      {showForm && (
        <section className="panel" id="report-section" aria-labelledby="report-heading">
          <h2 id="report-heading">Report an item</h2>
          <ReportForm onSubmit={addReport} onCancel={() => setShowForm(false)} />
        </section>
      )}

      <section aria-labelledby="items-heading">
        <h2 id="items-heading">Browse items</h2>
        <div className="filters">
          <label>
            Search
            <input
              type="search"
              placeholder="Item name or location"
              value={query}
              onChange={event => setQuery(event.target.value)}
            />
          </label>
          <label>
            Show
            <select value={filter} onChange={event => setFilter(event.target.value)}>
              {['All items', 'Lost', 'Found', 'My reports'].map(value => (
                <option key={value}>{value}</option>
              ))}
            </select>
          </label>
          <label>
            Category
            <select value={category} onChange={event => setCategory(event.target.value)}>
              <option>All categories</option>
              {categories.map(value => <option key={value}>{value}</option>)}
            </select>
          </label>
        </div>

        <p className="muted" role="status">
          {visibleItems.length} {visibleItems.length === 1 ? 'item' : 'items'}
        </p>
        <div className="item-list">
          {visibleItems.map(item => (
            <ItemCard key={item.id} item={item} onReturn={markReturned} />
          ))}
        </div>
        {visibleItems.length === 0 && (
          <p className="panel">No items found. Try changing the filters or add a report.</p>
        )}
      </section>

      <footer>
        Student prototype. Sample items are fictional. Your reports stay in this browser.
      </footer>
    </main>
  );
}
