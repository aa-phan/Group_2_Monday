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
  // Carried through only when present -- the insufficient-stock case (409)
  // is the one caller that needs these to say how many units are actually
  // on hand, per plan 02-04's interface contract.
  if (typeof body.onHand === 'number') {
    error.onHand = body.onHand;
  }
  if (typeof body.requested === 'number') {
    error.requested = body.requested;
  }
  if (body.field) {
    error.field = body.field;
  }
  throw error;
}

export async function fetchInventory(householdId, userId) {
  const params = new URLSearchParams({ householdId, userId });
  const response = await fetch(`/api/inventory?${params.toString()}`);

  if (!response.ok) {
    await throwForErrorResponse(response);
  }

  return response.json();
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

export async function restockItem(payload) {
  return postJson('/api/inventory/restock', payload);
}

export async function consumeItem(payload) {
  return postJson('/api/inventory/consume', payload);
}

export async function reserveItem(payload) {
  return postJson('/api/inventory/reserve', payload);
}

export async function releaseReservation(payload) {
  return postJson('/api/inventory/release', payload);
}
