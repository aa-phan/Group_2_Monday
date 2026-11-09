// The API modules have no access to React state, so when the server says
// the session is gone (a 401 from a data route) they announce it here and
// App.js decides what to show.

const listeners = new Set();

/**
 * Register a listener for "the server says you are signed out".
 * @param {() => void} listener
 * @returns {() => void} a function that removes the listener
 */
export function onSignedOut(listener) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/**
 * Tell every registered listener the session is gone. Iterates over a copy
 * so a listener that unsubscribes during the call is safe.
 */
export function notifySignedOut() {
  for (const listener of [...listeners]) {
    listener();
  }
}
