import os
import sys
from urllib.parse import parse_qs

import mongomock
import pytest
from flask.testing import FlaskClient

# Insert the server directory onto sys.path so the DB modules import by
# their bare names (hardwareDatabase, projectsDatabase, app).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as flask_app_module  # noqa: E402
import hardwareDatabase as hardwareDB  # noqa: E402


@pytest.fixture
def mongo():
    """A mongomock.MongoClient seeded with one project document."""
    client = mongomock.MongoClient()
    db = client[hardwareDB.DB_NAME]
    db[hardwareDB.PROJECTS_COLLECTION].insert_one(
        {"householdId": "H1", "users": ["alice", "bob"]}
    )
    return client


# Routes that establish or inspect the session themselves; the signing
# client must never pre-sign-in on these.
_AUTH_PATHS = ("/login", "/add_user", "/me", "/logout")


class SessionSigningClient(FlaskClient):
    """Test client that signs in as whatever userId each request claims.

    The data routes now require session['userId'] == the claimed userId
    (requireSessionUser). Most pre-existing tests are about other
    behavior and name their acting user in the body/query, so this client
    models "each request comes from the account it names". The claimed
    value is copied as-is (no str() coercion) so the strict xfails B1-B5,
    which send bad userId types, still reach the same code.
    """

    def open(self, *args, **kwargs):
        path = args[0] if args and isinstance(args[0], str) else ""
        if path.split("?", 1)[0] not in _AUTH_PATHS:
            claimed, body = self._claimedUser(path, kwargs)
            if claimed is not None and claimed != "":
                with self.session_transaction() as sess:
                    sess["userId"] = claimed
                    if isinstance(body, dict) and "userName" in body:
                        sess["username"] = body["userName"]
                    else:
                        sess["username"] = claimed
        return super().open(*args, **kwargs)

    @staticmethod
    def _claimedUser(path, kwargs):
        body = kwargs.get("json")
        if isinstance(body, dict) and "userId" in body:
            return body["userId"], body
        query = kwargs.get("query_string")
        if isinstance(query, (str, bytes)):
            query = parse_qs(query.decode() if isinstance(query, bytes) else query)
            if "userId" in query:
                return query["userId"][0], body
        elif isinstance(query, dict) and "userId" in query:
            return query["userId"], body
        if "?" in path:
            parsed = parse_qs(path.split("?", 1)[1])
            if "userId" in parsed:
                return parsed["userId"][0], body
        return None, body


@pytest.fixture
def api(mongo, monkeypatch):
    """A Flask test client with app.getMongoClient monkeypatched to return
    the seeded mongomock client, and which signs in as whatever userId each
    request claims (see SessionSigningClient). Pre-existing tests keep
    testing their own behavior; authorization itself is tested with
    bare_api in test_session_authorization.py.
    """
    monkeypatch.setattr(flask_app_module, "getMongoClient", lambda: mongo)
    monkeypatch.setattr(flask_app_module.app, "test_client_class", SessionSigningClient)
    flask_app_module.app.testing = True
    return flask_app_module.app.test_client()


@pytest.fixture
def bare_api(mongo, monkeypatch):
    """A plain Flask test client (no automatic sign-in) with
    app.getMongoClient monkeypatched to the seeded mongomock client. Used
    to test the session guard itself.
    """
    monkeypatch.setattr(flask_app_module, "getMongoClient", lambda: mongo)
    flask_app_module.app.testing = True
    return flask_app_module.app.test_client()


@pytest.fixture
def sign_in():
    """sign_in(client, userId, username=None): write a signed-in session
    onto the client's cookie jar without going through /login.
    """
    def _sign_in(client, userId, username=None):
        with client.session_transaction() as sess:
            sess["userId"] = userId
            sess["username"] = userId if username is None else username
    return _sign_in


@pytest.fixture
def seed_set(mongo):
    """seed_set(projectId, hwSetName, capacity) -> serialized hardware set."""
    def _seed(projectId, hwSetName, capacity):
        return hardwareDB.createHardwareSet(mongo, projectId, hwSetName, capacity)
    return _seed
