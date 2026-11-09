import { useState } from 'react';
import { api } from '../api';

const headings = {
  login: 'Sign in to the campus board',
  register: 'Create your SCU account',
  verify: 'Verify your SCU email',
};

export default function AccountForm({ onLogin, pending, setPending }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  function switchMode(next) {
    setMode(next);
    setError('');
    setNotice('');
  }

  async function submit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const body = Object.fromEntries(new FormData(form));
    const sendCode = event.nativeEvent.submitter?.value === 'send-code';
    setPending(true);
    setError('');
    setNotice('');
    try {
      if (mode === 'login') {
        const { user } = await api('/api/auth/login/', { method: 'POST', body });
        onLogin(user);
      } else if (mode === 'register') {
        const { message } = await api('/api/auth/register/', { method: 'POST', body });
        switchMode('verify');
        setNotice(message + ' Use Send code below to continue.');
      } else if (sendCode) {
        const { message } = await api('/api/auth/verification/request/', {
          method: 'POST', body: { email },
        });
        setNotice(message);
      } else {
        const { message } = await api('/api/auth/verification/confirm/', { method: 'POST', body });
        switchMode('login');
        setNotice(message);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="panel account" aria-labelledby="account-heading">
      <h2 id="account-heading">{headings[mode]}</h2>
      <p className="muted">Use your @scu.edu email to access shared reports.</p>
      {error && <p className="error" role="alert">{error}</p>}
      {notice && <p className="message" role="status">{notice}</p>}
      <form key={mode} onSubmit={submit}>
        <fieldset disabled={pending}>
          {mode === 'register' && (
            <label>Full name<input name="full_name" required autoComplete="name" /></label>
          )}
          <label>
            SCU email
            <input name="email" type="email" autoComplete="email" required placeholder="you@scu.edu"
              value={email} onChange={event => setEmail(event.target.value)} />
          </label>
          {mode === 'verify' ? (
            <label>
              Verification code
              <input name="code" required inputMode="numeric" autoComplete="one-time-code"
                pattern="[0-9]{6}" maxLength={6} placeholder="Six digits" />
            </label>
          ) : (
            <label>
              Password
              <input name="password" type="password" required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
            </label>
          )}
          <div className="form-actions">
            <button type="submit">{mode === 'login' ? 'Sign in' : mode === 'register' ? 'Create account' : 'Verify email'}</button>
            {mode === 'verify' && (
              <button type="submit" value="send-code" className="secondary" formNoValidate
                onClick={event => {
                  if (!event.currentTarget.form.elements.email.reportValidity()) event.preventDefault();
                }}>Send code</button>
            )}
            {mode !== 'login' && <button type="button" className="secondary" onClick={() => switchMode('login')}>Back to sign in</button>}
          </div>
          {mode === 'login' && (
            <div className="form-actions account-options">
              <button type="button" className="text-button" onClick={() => switchMode('register')}>Create an account</button>
              <button type="button" className="text-button" onClick={() => switchMode('verify')}>Verify my email</button>
            </div>
          )}
        </fieldset>
      </form>
    </section>
  );
}
