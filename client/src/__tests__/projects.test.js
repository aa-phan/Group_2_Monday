import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { joinProject } from '../api/projects.js';

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('joinProject', () => {
  it('POSTs projectId and userId to /join_project and returns the body', async () => {
    fetch.mockResolvedValue(jsonResponse(200, { userId: 'alice1', projectId: 'P1' }));

    const data = await joinProject({ projectId: 'P1', userId: 'alice1' });

    expect(fetch).toHaveBeenCalledWith('/join_project', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ projectId: 'P1', userId: 'alice1' }),
    });
    expect(data).toEqual({ userId: 'alice1', projectId: 'P1' });
  });

  it('throws an Error carrying the server error code on a non-ok response', async () => {
    fetch.mockResolvedValue(jsonResponse(404, { error: 'project_not_found', field: 'projectId' }));

    const error = await joinProject({ projectId: 'NoSuchProject', userId: 'alice1' }).catch(
      (caught) => caught
    );

    expect(error.message).toBe('project_not_found');
    expect(error.field).toBe('projectId');
  });

  it('falls back to a status message when the body has no error field', async () => {
    fetch.mockResolvedValue(jsonResponse(500, {}));

    await expect(joinProject({ projectId: 'P1', userId: 'alice1' })).rejects.toThrow(
      'Request failed with status 500'
    );
  });
});
