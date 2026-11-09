let csrfToken;

export async function api(path, { method = 'GET', body, signal } = {}) {
  const headers = { Accept: 'application/json' };
  if (method !== 'GET') {
    if (!csrfToken) {
      ({ csrfToken } = await api('/api/auth/csrf/'));
    }
    headers['X-CSRFToken'] = csrfToken;
    if (body && !(body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(body);
    }
  }

  let response;
  try {
    response = await fetch(path, { method, headers, body, signal, credentials: 'same-origin' });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('Could not reach the campus server. Try again or switch to the demo board.');
  }
  const isJson = response.headers.get('Content-Type')?.includes('application/json');
  const data = isJson ? await response.json() : {};
  if (!response.ok || !isJson) {
    if (response.status === 403 && !isJson) csrfToken = undefined;
    const details = Object.values(data.errors || {}).flat().join(' ');
    const message = response.status === 403 && !isJson
      ? 'Your security token expired. Please try again.'
      : 'The campus server is unavailable. Check that Django is running or switch to the demo board.';
    throw Object.assign(new Error(details || message), { status: response.status });
  }

  if (data.csrfToken) csrfToken = data.csrfToken;
  return data;
}

export function toBoardItem(report, userId) {
  return {
    id: report.id,
    title: report.title,
    type: report.item_type_display,
    category: report.category_display,
    date: report.happened_on,
    time: report.happened_time,
    location: report.location_display,
    locationCode: report.location,
    locationDetails: report.location_details,
    description: report.description,
    resolved: report.is_resolved,
    pinned: report.is_pinned,
    image: report.image_url,
    author: report.author.full_name,
    isOwn: report.author.id === userId,
  };
}
