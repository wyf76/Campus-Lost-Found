export const categories = ['Electronics', 'Bags', 'Keys', 'Clothing', 'Books', 'Other'];

// All sample reports are fictional. New reports are stored separately in the browser.
export const sampleItems = [
  { id: 'demo-1', title: 'Black everyday backpack', type: 'Lost', category: 'Bags', location: 'Learning Commons', date: '2026-10-20', description: 'A black backpack with a small red keychain, last seen near the study tables on the first floor.', contact: '', resolved: false },
  { id: 'demo-2', title: 'Stainless steel water bottle', type: 'Found', category: 'Other', location: 'Benson Center', date: '2026-10-21', description: 'A sage green water bottle left on a table outside Benson Center. Tell the reporter what stickers are on it to help identify it.', contact: '', resolved: false },
  { id: 'demo-3', title: 'Keys with a blue lanyard', type: 'Found', category: 'Keys', location: 'SCDI', date: '2026-10-21', description: 'A set of keys with a blue lanyard, found near the main entrance. Be ready to describe the keys.', contact: '', resolved: false },
  { id: 'demo-4', title: 'Wireless headphones', type: 'Lost', category: 'Electronics', location: 'Malley Center', date: '2026-10-19', description: 'Cream over-ear headphones, possibly left near the benches after an afternoon workout.', contact: '', resolved: false },
  { id: 'demo-5', title: 'Green spiral notebook', type: 'Found', category: 'Books', location: 'Engineering Quad', date: '2026-10-20', description: 'A green notebook containing handwritten class notes. Describe the subject to identify it.', contact: '', resolved: false },
  { id: 'demo-6', title: 'Favorite gray hoodie', type: 'Lost', category: 'Clothing', location: 'Orradre Library', date: '2026-10-18', description: 'A gray hoodie, size medium. Last seen on the back of a chair in the library.', contact: '', resolved: false },
];

export function formatDate(date) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(`${date}T12:00:00`));
}
