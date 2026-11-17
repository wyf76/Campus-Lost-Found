import { useEffect, useRef, useState } from 'react';
import { api } from '../api';

export default function MessageInbox({ userId, initialConversationId, pending, runAction, onSessionExpired }) {
  const heading = useRef(null);
  const [conversationId, setConversationId] = useState(initialConversationId);
  const [revision, setRevision] = useState(0);
  const [inbox, setInbox] = useState(null);
  const [loadError, setLoadError] = useState('');
  const [draft, setDraft] = useState('');
  const messagePath = conversationId === null ? null : '/api/conversations/' + conversationId + '/messages/';

  useEffect(() => heading.current?.focus(), []);

  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };
    Promise.all([
      api('/api/conversations/', options),
      messagePath ? api(messagePath, options) : { messages: [] },
    ]).then(([{ conversations }, { messages }]) => {
      if (controller.signal.aborted) return;
      setInbox({ conversations, messages, conversationId, revision });
      setLoadError('');
    }).catch(error => {
      if (controller.signal.aborted) return;
      if (error.status === 401) onSessionExpired();
      else setLoadError(error.message);
    });
    return () => controller.abort();
  }, [conversationId, messagePath, onSessionExpired, revision]);

  const conversation = inbox?.conversations.find(entry => entry.id === conversationId);
  const messages = inbox?.conversationId === conversationId ? inbox.messages : [];
  const loading = !loadError && (inbox?.conversationId !== conversationId || inbox?.revision !== revision);

  function refresh() {
    setLoadError('');
    setRevision(current => current + 1);
  }

  function openConversation(id) {
    if (id === conversationId) return;
    setLoadError('');
    setDraft('');
    setConversationId(id);
  }

  async function sendMessage(event) {
    event.preventDefault();
    const body = draft.trim();
    if (!body || pending || loading || loadError || !conversation || conversation.report.is_resolved) return;

    const sent = await runAction(async () => {
      try {
        await api(messagePath, { method: 'POST', body: { body } });
      } catch (error) {
        if (error.status === 409) refresh();
        throw error;
      }
    });
    if (sent) {
      setDraft('');
      refresh();
    }
  }

  return (
    <section aria-labelledby="messages-heading">
      <div className="board-heading">
        <h1 id="messages-heading" ref={heading} tabIndex={-1}>Messages</h1>
        <button type="button" className="secondary" disabled={pending || loading}
          onClick={refresh}>Refresh messages</button>
      </div>
      {loadError && <p className="error" role="alert">{loadError}</p>}
      {loading && <p className="muted" role="status">Loading messages…</p>}
      {inbox?.conversations.length === 0 && (
        <div className="panel empty">
          <h2>No conversations yet</h2>
          <p className="muted">Choose <strong>Contact poster</strong> on an open report to start a conversation.</p>
        </div>
      )}
      {inbox?.conversations.length > 0 && (
        <div className="message-inbox">
          <nav className="panel conversation-list" aria-label="Conversations">
            {inbox.conversations.map(entry => (
              <button type="button" key={entry.id} className="secondary conversation-button"
                aria-pressed={entry.id === conversationId} disabled={pending}
                onClick={() => openConversation(entry.id)}>
                <strong>{entry.report.title}</strong>
                <span>{entry.other_participant.full_name}{entry.report.is_resolved ? ' · Returned' : ''}</span>
              </button>
            ))}
          </nav>
          {conversation ? (
            <div className="panel message-thread">
              <h2>{conversation.report.title}</h2>
              <p className="muted">Conversation with {conversation.other_participant.full_name}</p>
              {messages.length > 0 && (
                <ol className="message-list" aria-label="Conversation messages">
                  {messages.map(message => (
                    <li key={message.id}>
                      <p className="muted">
                        <strong>{message.sender.id === userId ? 'You' : message.sender.full_name}</strong>
                        {' · '}<time dateTime={message.created_at}>{new Date(message.created_at).toLocaleString()}</time>
                      </p>
                      <p className="description">{message.body}</p>
                    </li>
                  ))}
                </ol>
              )}
              {!messages.length && !loading && !loadError && <p className="muted">No messages yet.</p>}
              {conversation.report.is_resolved ? (
                <p className="muted">This item has been returned. You can still read the conversation here.</p>
              ) : (
                <form onSubmit={sendMessage}>
                  <label>
                    Your message
                    <textarea rows={3} value={draft} onChange={event => setDraft(event.target.value)}
                      placeholder="Ask about the item or arrange pickup" required maxLength={4000} disabled={pending} />
                  </label>
                  <button type="submit" disabled={pending || loading || Boolean(loadError) || !draft.trim()}>
                    {pending ? 'Sending…' : 'Send message'}
                  </button>
                </form>
              )}
            </div>
          ) : (
            <div className="panel">
              <p className="muted">{conversationId === null ? 'Choose a conversation.' : 'Conversation unavailable.'}</p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
