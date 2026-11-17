import { useCallback, useEffect, useState } from 'react';
import { api, toBoardItem } from './api';
import AccountForm from './components/AccountForm';
import ItemCard from './components/ItemCard';
import MessageInbox from './components/MessageInbox';
import ModerationDashboard from './components/ModerationDashboard';
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

const views = ['All items', 'Lost', 'Found', 'Returned', 'My reports'];
const reportEndpoints = {
  Returned: '/api/reports/?status=resolved',
  'My reports': '/api/users/me/reports/',
};

export default function App() {
  const [reports, setReports] = useState(loadReports);
  const [campus, setCampus] = useState(() => new URLSearchParams(location.search).get('board') === 'campus');
  const [user, setUser] = useState(undefined);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('All items');
  const [category, setCategory] = useState('All categories');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const [storageError, setStorageError] = useState(false);
  const [revision, setRevision] = useState(0);
  const [board, setBoard] = useState(null);
  const [campusView, setCampusView] = useState('board');
  const [initialConversationId, setInitialConversationId] = useState(null);
  const canModerate = campus && Boolean(user?.is_moderator);
  const moderating = canModerate && campusView === 'moderation';
  const messaging = campus && Boolean(user) && campusView === 'messages';
  const browsingBoard = !moderating && !messaging;

  const expireSession = useCallback(() => {
    setError('Your session expired. Sign in to continue.');
    setUser(null);
    setShowForm(false);
    setEditing(null);
    setCampusView('board');
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(reports));
      setStorageError(false);
    } catch {
      setStorageError(true);
    }
  }, [reports]);

  useEffect(() => {
    if (!campus || user !== undefined) return;
    const controller = new AbortController();
    api('/api/users/me/', { signal: controller.signal }).then(({ user }) => {
      if (!controller.signal.aborted) setUser(user);
    }).catch(error => {
      if (controller.signal.aborted) return;
      setUser(null);
      if (error.status !== 401) setError(error.message);
    });
    return () => controller.abort();
  }, [campus, user]);

  const endpoint = reportEndpoints[filter] ?? '/api/reports/';
  useEffect(() => {
    if (!campus || !user || !browsingBoard) return;
    const controller = new AbortController();
    api(endpoint, { signal: controller.signal }).then(({ reports }) => {
      if (controller.signal.aborted) return;
      setBoard({ endpoint, userId: user.id, revision, items: reports.map(report => toBoardItem(report, user.id)) });
    }).catch(error => {
      if (controller.signal.aborted) return;
      if (error.status === 401) {
        expireSession();
      } else {
        setBoard({ endpoint, userId: user.id, revision, error: error.message });
      }
    });
    return () => controller.abort();
  }, [browsingBoard, campus, endpoint, expireSession, revision, user]);

  const boardReady = board?.endpoint === endpoint && board?.userId === user?.id && board?.revision === revision;
  const boardError = campus && boardReady ? board.error : '';
  const canBrowse = !campus || Boolean(user);
  const loading = campus && canBrowse && !boardReady;
  const items = campus ? (boardReady ? board.items || [] : []) : [...reports, ...sampleItems];
  const visibleItems = items.filter(item => {
    const matchesView = (filter === 'My reports' && item.isOwn)
      || (filter === 'Returned' && item.resolved)
      || (!item.resolved && (filter === 'All items' || item.type === filter));
    const matchesCategory = category === 'All categories' || item.category === category;
    const text = [item.title, item.location, item.locationDetails, item.description].join(' ').toLowerCase();
    return matchesView && matchesCategory && text.includes(query.trim().toLowerCase());
  });

  function closeForm() {
    setShowForm(false);
    setEditing(null);
  }

  function switchBoard(next) {
    const url = new URL(location.href);
    if (next) url.searchParams.set('board', 'campus');
    else url.searchParams.delete('board');
    history.replaceState(null, '', url);
    setCampus(next);
    setBoard(null);
    setUser(undefined);
    setFilter('All items');
    setQuery('');
    setCategory('All categories');
    setMessage('');
    setError('');
    setCampusView('board');
    closeForm();
  }

  function completeReport(text) {
    closeForm();
    setFilter('My reports');
    setQuery('');
    setCategory('All categories');
    setMessage(text);
  }

  async function runAction(action) {
    setPending(true);
    setError('');
    setMessage('');
    try {
      await action();
      return true;
    } catch (error) {
      if (error.status === 401) {
        expireSession();
      } else {
        setError(error.message);
      }
      return false;
    } finally {
      setPending(false);
    }
  }

  function saveReport(body) {
    if (!campus) {
      setReports(current => [body, ...current]);
      completeReport('Report added to My reports.');
      return;
    }

    runAction(async () => {
      const path = editing ? '/api/reports/' + editing.id + '/edit/' : '/api/reports/';
      await api(path, { method: editing ? 'PATCH' : 'POST', body });
      setRevision(current => current + 1);
      completeReport(editing ? 'Report updated.' : 'Report posted to the campus board.');
    });
  }

  function markReturned(id) {
    runAction(async () => {
      if (campus) {
        await api('/api/reports/' + id + '/resolve/', { method: 'POST' });
        setRevision(current => current + 1);
      } else {
        setReports(current => current.map(item => item.id === id ? { ...item, resolved: true } : item));
      }

      if (editing?.id === id) closeForm();
      setFilter('Returned');
      setQuery('');
      setCategory('All categories');
      setMessage('Item marked as returned. It remains in My reports.');
    });
  }

  function flagReport(id, reason) {
    return runAction(async () => {
      await api('/api/reports/' + id + '/flag/', { method: 'POST', body: { reason } });
    });
  }

  function openCampusView(view, conversationId = null) {
    setCampusView(view);
    setInitialConversationId(conversationId);
    setError('');
    setMessage('');
    closeForm();
  }

  function contactPoster(id) {
    return runAction(async () => {
      const { conversation } = await api('/api/reports/' + id + '/conversations/', { method: 'POST' });
      openCampusView('messages', conversation.id);
    });
  }

  function refreshReports() {
    setRevision(current => current + 1);
  }

  function moderateReport(path, method, feedback) {
    return runAction(async () => {
      await api(path, { method });
      refreshReports();
      setMessage(feedback);
    });
  }

  function signOut() {
    runAction(async () => {
      await api('/api/auth/logout/', { method: 'POST' });
      setUser(null);
      setBoard(null);
      setCampusView('board');
      closeForm();
    });
  }

  return (
    <>
      <div className="masthead">
        <div className="container masthead-inner">
          <span className="brand">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 10c0 4-7 10-7 10S5 14 5 10a7 7 0 1 1 14 0Z" /><circle cx="12" cy="10" r="2.2" /></svg>
            Santa Clara University
          </span>
          <div className="account-nav">
            {campus && user && (
              <button className="secondary" disabled={pending}
                onClick={() => openCampusView(messaging ? 'board' : 'messages')}>
                {messaging ? 'Campus board' : 'Messages'}
              </button>
            )}
            {canModerate && (
              <button className="secondary" disabled={pending}
                onClick={() => openCampusView(moderating ? 'board' : 'moderation')}>
                {moderating ? 'Campus board' : 'Moderation'}
              </button>
            )}
            {campus && user && <button className="text-button" disabled={pending} onClick={signOut}>Sign out</button>}
            <button className="secondary" disabled={pending} onClick={() => switchBoard(!campus)}>
              {campus ? 'Open demo board' : 'SCU sign in'}
            </button>
          </div>
        </div>
      </div>
      <main className="container">
        {browsingBoard && <header className="hero">
          <div>
            <p className="eyebrow">{campus ? 'SCU campus board' : 'Lab 7 · Demo board'}</p>
            <h1>Campus Lost &amp; Found</h1>
            <p>Find what you’ve lost or help return something to a fellow Bronco.</p>
            {canBrowse && (
              <button type="button" disabled={pending} aria-expanded={showForm}
                aria-controls={showForm ? 'report-section' : undefined}
                onClick={() => showForm ? closeForm() : setShowForm(true)}>
                {showForm ? 'Close report form' : '+ Report an item'}
              </button>
            )}
          </div>
          <svg className="hero-art" viewBox="0 0 180 136" aria-hidden="true">
            <circle cx="95" cy="64" r="56" fill="#fae2df" />
            <path d="M43 112h105M55 98l15-48 39 11 25-9-15 48-28 9zM70 50l-9 48m48-37-18 48" fill="#fff8f2" />
            <path d="M117 40c0 16-22 33-22 33S73 56 73 40a22 22 0 1 1 44 0z" fill="#ad273d" />
            <circle cx="95" cy="40" r="7.5" fill="#fff8f2" />
            <path d="M143 29v12m-6-6h12M42 43v9m-4.5-4.5h9M145 87v9m-4.5-4.5h9" />
          </svg>
        </header>}

        {message && <p className="message" role="status">{message}</p>}
        {error && <p className="error" role="alert">{error}</p>}
        {!campus && storageError && <p role="alert">Browser storage is unavailable. New changes will be lost after a refresh.</p>}

        {campus && user === undefined && <p role="status">Checking your campus session…</p>}
        {campus && user === null && <AccountForm pending={pending} setPending={setPending} onLogin={user => {
          setError('');
          setFilter('All items');
          setBoard(null);
          setUser(user);
        }} />}

        {moderating && (
          <ModerationDashboard user={user} pending={pending} revision={revision}
            onAction={moderateReport} onRetry={refreshReports} onSessionExpired={expireSession} />
        )}

        {messaging && (
          <MessageInbox key={user.id} userId={user.id} initialConversationId={initialConversationId}
            pending={pending} runAction={runAction} onSessionExpired={expireSession} />
        )}

        {canBrowse && browsingBoard && showForm && (
          <section className="panel report-section" id="report-section" aria-labelledby="report-heading">
            <h2 id="report-heading">{editing ? 'Edit report' : 'Report an item'}</h2>
            <ReportForm key={editing?.id || 'new'} campus={campus} editing={editing}
              pending={pending} onSubmit={saveReport} onCancel={closeForm} />
          </section>
        )}

        {canBrowse && browsingBoard && (
          <section aria-labelledby="items-heading">
            <div className="board-heading">
              <div>
                <h2 id="items-heading">Browse items</h2>
                <p className="muted">{campus ? 'Signed in as ' + user.full_name : 'Explore sample posts or try a practice report.'}</p>
              </div>
              {!loading && !boardError && (
                <p className="result-count" role="status">{visibleItems.length} {visibleItems.length === 1 ? 'item' : 'items'}</p>
              )}
            </div>
            <div className="board-controls">
              <div className="view-buttons" role="group" aria-label="Report view">
                {views.map(value => (
                  <button type="button" className="view-button" key={value}
                    aria-pressed={value === filter} onClick={() => setFilter(value)}>{value}</button>
                ))}
              </div>
              <div className="filters">
                <label>
                  Search
                  <input type="search" placeholder="Item name or location" value={query}
                    onChange={event => setQuery(event.target.value)} />
                </label>
                <label>
                  Category
                  <select value={category} onChange={event => setCategory(event.target.value)}>
                    <option>All categories</option>
                    {categories.map(value => <option key={value}>{value}</option>)}
                  </select>
                </label>
              </div>
            </div>
            {loading && <p role="status">Loading reports…</p>}
            {boardError && (
              <div className="panel">
                <p className="error" role="alert">{boardError}</p>
                <button className="secondary" onClick={() => setRevision(current => current + 1)}>Try again</button>
              </div>
            )}
            {!loading && !boardError && (
              visibleItems.length ? (
                <div className="item-list">
                  {visibleItems.map(item => (
                    <ItemCard key={item.id} item={item} pending={pending} onReturn={markReturned}
                      onContact={campus && !item.isOwn && !item.resolved ? contactPoster : undefined}
                      onFlag={campus && !item.isOwn ? flagReport : undefined}
                      onEdit={campus ? item => {
                        setEditing(item);
                        setError('');
                        setMessage('');
                        setShowForm(true);
                        requestAnimationFrame(() => document.getElementById('report-section')?.scrollIntoView());
                      } : undefined} />
                  ))}
                </div>
              ) : (
                <div className="panel empty">
                  <h3>No matching reports</h3>
                  <p className="muted">Try a different search or filter, or report an item.</p>
                </div>
              )
            )}
          </section>
        )}

        <footer>
          {campus ? 'Campus Lost & Found · Santa Clara University student project' : 'Lab 7 prototype · Fictional sample items · Practice reports stay in this browser'}
        </footer>
      </main>
    </>
  );
}
