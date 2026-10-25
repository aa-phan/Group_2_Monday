async function parseErrorBody(response) {
  try {
    const body = await response.json();
    return body || {};
  } catch (parseError) {
    return {};
  }
}

async function throwForErrorResponse(response) {
  const body = await parseErrorBody(response);
  const message = body.error ? body.error : `Request failed with status ${response.status}`;
  const error = new Error(message);
  if (body.field) {
    error.field = body.field;
  }
  throw error;
}

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    await throwForErrorResponse(response);
  }

  return response.json();
}

// US-04 -- add userId to projectId's membership list. Idempotent on the
// server (joining twice is a no-op), so this is safe to call on every
// sign-in/sign-up, not just once.
export async function joinProject({ projectId, userId }) {
  return postJson('/join_project', { projectId, userId });
}
