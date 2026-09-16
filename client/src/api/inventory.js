async function parseErrorBody(response) {
  try {
    const body = await response.json();
    return body && body.error ? body.error : `Request failed with status ${response.status}`;
  } catch (parseError) {
    return `Request failed with status ${response.status}`;
  }
}

export async function fetchInventory(householdId, userId) {
  const params = new URLSearchParams({ householdId, userId });
  const response = await fetch(`/api/inventory?${params.toString()}`);

  if (!response.ok) {
    throw new Error(await parseErrorBody(response));
  }

  return response.json();
}

export async function restockItem(payload) {
  const response = await fetch('/api/inventory/restock', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(await parseErrorBody(response));
  }

  return response.json();
}
