import { useEffect, useState } from 'react';
import { api, toBoardItem } from '../api';
import ItemCard from './ItemCard';

function ConfirmAction({ label, prompt, pending, onConfirm }) {
  const [confirming, setConfirming] = useState(false);

  if (!confirming) {
    return <button type="button" className="secondary" disabled={pending}
      onClick={() => setConfirming(true)}>{label}</button>;
  }

  return (
    <div className="action-confirmation">
      <p>{prompt}</p>
      <div className="form-actions">
        <button type="button" disabled={pending} onClick={async () => {
          if (await onConfirm()) setConfirming(false);
        }}>Confirm {label.toLowerCase()}</button>
        <button type="button" className="secondary" disabled={pending}
          onClick={() => setConfirming(false)}>Cancel</button>
      </div>
    </div>
  );
}

function ModerationStats({ stats }) {
  const { reports, flags, students } = stats;
  const metrics = [
    ['Open reports', reports.open],
    ['Returned reports', reports.resolved],
    ['Flags awaiting escalation', flags.total - flags.escalated],
    ['Escalated flags', flags.escalated],
    ['Active verified students', students.active_verified],
  ];

  return (
    <dl className="moderation-stats" aria-label="Campus statistics">
      {metrics.map(([label, count]) => (
        <div className="panel" key={label}>
          <dt>{label}</dt>
          <dd>{count}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function ModerationDashboard({ user, pending, revision, onAction, onRetry, onSessionExpired }) {
  const [dashboard, setDashboard] = useState(null);
  const [loadError, setLoadError] = useState('');
  const [status, setStatus] = useState('All statuses');
  const [query, setQuery] = useState('');
  const [selectedReport, setSelectedReport] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };
    Promise.all([
      api('/api/moderation/reports/', options),
      api('/api/reports/flags/', options),
      api('/api/moderation/statistics/', options),
      api('/api/users/blocked/', options),
    ]).then(([{ reports }, { flags }, stats, { students: blockedStudents }]) => {
      if (controller.signal.aborted) return;
      setDashboard({ reports, flags, stats, blockedStudents });
      setLoadError('');
    }).catch(error => {
      if (controller.signal.aborted) return;
      if (error.status === 401) onSessionExpired();
      else setLoadError(error.message);
    });
    return () => controller.abort();
  }, [onSessionExpired, revision]);

  const blockedIds = new Set(dashboard?.blockedStudents.map(student => student.id));
  const reports = dashboard?.reports.filter(report => {
    if (selectedReport !== null) return report.id === selectedReport;
    const matchesStatus = status === 'All statuses' || report.is_resolved === (status === 'Returned');
    const text = [report.title, report.author.full_name].join(' ').toLowerCase();
    return matchesStatus && text.includes(query.trim().toLowerCase());
  });

  function reviewReport(id) {
    setSelectedReport(id);
    document.getElementById('moderation-history-heading')?.focus();
  }

  return (
    <section aria-labelledby="moderation-heading">
      <h1 id="moderation-heading">Moderation</h1>
      {loadError && (
        <div className="panel">
          <p className="error" role="alert">{loadError}</p>
          <button type="button" className="secondary" onClick={onRetry}>Try again</button>
        </div>
      )}
      {!loadError && !dashboard && <p role="status">Loading moderation dashboard…</p>}
      {!loadError && dashboard && (
        <>
          <ModerationStats stats={dashboard.stats} />
          <section aria-labelledby="blocked-students-heading">
            <h2 id="blocked-students-heading">Blocked students</h2>
            {dashboard.blockedStudents.length ? (
              <ul className="moderation-list">
                {dashboard.blockedStudents.map(student => (
                  <li className="panel moderation-row" key={student.id}>
                    <div>
                      <h3>{student.full_name}</h3>
                      <p className="muted">{student.email}</p>
                    </div>
                    <div className="form-actions">
                      <ConfirmAction label="Unblock" pending={pending}
                        prompt={'Restore campus board access for ' + student.full_name + '?'}
                        onConfirm={() => onAction('/api/users/' + student.id + '/unblock/',
                          'POST', 'Student account unblocked.')} />
                    </div>
                  </li>
                ))}
              </ul>
            ) : <p className="muted">No blocked students.</p>}
          </section>
          <section aria-labelledby="moderation-flags-heading">
            <h2 id="moderation-flags-heading">Flagged reports</h2>
            {dashboard.flags.length ? (
              <ul className="moderation-list">
                {dashboard.flags.map(flag => (
                  <li className="panel moderation-row" key={flag.id}>
                    <div>
                      <h3>{flag.report_title}</h3>
                      <p className="description">{flag.reason}</p>
                      {flag.escalated_at && (
                        <p className="muted">Escalated {new Date(flag.escalated_at).toLocaleDateString()}</p>
                      )}
                    </div>
                    <div className="form-actions">
                      <button type="button" className="secondary" disabled={pending}
                        onClick={() => reviewReport(flag.report_id)}>Review report</button>
                      {!flag.escalated_at && (
                        <ConfirmAction label="Escalate flag" pending={pending}
                          prompt="Send this flag and the report author’s email to university staff?"
                          onConfirm={() => onAction('/api/reports/flags/' + flag.id + '/escalate/',
                            'POST', 'Flag escalated to university staff.')} />
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : <p className="muted">No flagged reports.</p>}
          </section>
          <section aria-labelledby="moderation-history-heading">
            <h2 id="moderation-history-heading" tabIndex={-1}>Report history</h2>
            <div className="board-controls">
              {selectedReport !== null ? (
                <button type="button" className="secondary" onClick={() => setSelectedReport(null)}>
                  Back to report history
                </button>
              ) : (
                <div className="filters">
                  <label>
                    Search reports
                    <input type="search" value={query} placeholder="Item name or author"
                      onChange={event => setQuery(event.target.value)} />
                  </label>
                  <label>
                    Status
                    <select value={status} onChange={event => setStatus(event.target.value)}>
                      <option>All statuses</option>
                      <option>Open</option>
                      <option>Returned</option>
                    </select>
                  </label>
                </div>
              )}
            </div>
            {reports.length ? (
              <div className="item-list">
                {reports.map(report => {
                  const item = toBoardItem(report, user.id);
                  const path = '/api/reports/' + item.id;
                  const authorBlocked = blockedIds.has(report.author.id);
                  const canBlockAuthor = !item.isOwn && !authorBlocked;
                  return (
                    <ItemCard key={item.id} item={item}>
                      {authorBlocked && <p className="muted">Author blocked</p>}
                      {(!item.resolved || canBlockAuthor) && (
                        <div className="form-actions card-actions">
                          {!item.resolved && (
                            <>
                              <button type="button" className="secondary" disabled={pending}
                                onClick={() => onAction(path + '/pin/', item.pinned ? 'DELETE' : 'POST',
                                  item.pinned ? 'Report unpinned.' : 'Report pinned.')}>
                                {item.pinned ? 'Unpin report' : 'Pin report'}
                              </button>
                              <ConfirmAction label="Mark as returned" pending={pending}
                                prompt={'Move “' + item.title + '” to Returned?'}
                                onConfirm={() => onAction(path + '/resolve/', 'POST', 'Report marked as returned.')} />
                            </>
                          )}
                          {canBlockAuthor && (
                            <ConfirmAction label="Block author" pending={pending}
                              prompt={'Block ' + item.author + ' from signing in to the campus board?'}
                              onConfirm={() => onAction('/api/users/' + report.author.id + '/block/',
                                'POST', 'Student account blocked.')} />
                          )}
                        </div>
                      )}
                    </ItemCard>
                  );
                })}
              </div>
            ) : <p className="muted">No matching reports.</p>}
          </section>
        </>
      )}
    </section>
  );
}
