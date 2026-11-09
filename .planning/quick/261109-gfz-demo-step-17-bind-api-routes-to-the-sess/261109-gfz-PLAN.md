---
phase: 261109-gfz-demo-step-17-bind-api-routes-to-the-sess
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - server/app.py
  - server/tests/conftest.py
  - server/tests/test_session_authorization.py
  - server/tests/test_api_contract.py
  - AUTH.md
  - client/src/api/sessionEvents.js
  - client/src/api/hardware.js
  - client/src/api/projects.js
  - client/src/App.js
  - client/src/__tests__/session-expired.test.js
autonomous: true
requirements:
  - PROJ-02
  - ACCT-04

estimate:
  tokens: 60000
  raw_tokens: 60000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "A request with no session to any of the 10 project/hardware routes (/join_project, /get_user_projects_list, /create_project, /get_project_info, GET /api/hardware, /api/hardware/checkin|checkout|request|release|rename|set_active) gets 401 {\"error\": \"not_signed_in\"}. Nothing is written, and the database is never opened (D-01, D-02)"
    - "A signed-in user who sends someone else's userId gets 403 {\"error\": \"forbidden_user_mismatch\"} and nothing is written. Demo step 17: a TA signed in as themselves cannot join or act on a project as an existing member by typing that member's userId (D-01, D-02)"
    - "A signed-in user acting as themselves gets the same responses as before. Missing-field 400s still come first, non-members still get 403 not_a_project_member, and check-in accountability stays per-project as PR #14 left it (D-02, D-04, D-09)"
    - "POST /api/hardware/request stores the session's username as the requester and ignores any userName in the body (D-03)"
    - "A route added to server/app.py without a row in the session-authorization route table fails the guard test (D-06)"
    - "When any hardware or project API call gets a 401, the client drops the signed-in state and shows the sign-in view (D-08)"
    - "The server suite passes with exactly 17 xfailed. The client suite passes and the production build succeeds (D-05, D-08)"
  artifacts:
    - path: "server/app.py"
      provides: "NotSignedInError and SessionUserMismatchError with their errorhandlers, plus requireSessionUser(claimedUserId), called from all 10 routes"
      contains: "def requireSessionUser"
    - path: "server/tests/conftest.py"
      provides: "api fixture that signs in as whatever userId each request claims, plus bare_api and sign_in fixtures"
      contains: "session_transaction"
    - path: "server/tests/test_session_authorization.py"
      provides: "Route-table-driven 401/403/success/non-member tests for all 10 routes, the session-username test for /request, and the url_map guard"
      contains: "url_map"
    - path: "server/tests/test_api_contract.py"
      provides: "503 database_not_configured test signs in first, so it still reaches getMongoClient"
      contains: "sign_in"
    - path: "AUTH.md"
      provides: "The paragraph that described the trust-the-userId gap now describes the enforced session binding"
      contains: "forbidden_user_mismatch"
    - path: "client/src/api/sessionEvents.js"
      provides: "notifySignedOut / onSignedOut publish-subscribe"
      contains: "onSignedOut"
    - path: "client/src/__tests__/session-expired.test.js"
      provides: "Unit tests for sessionEvents, plus App-level tests: a 401 from api/projects.js or api/hardware.js returns to the sign-in view"
      contains: "not_signed_in"
  key_links:
    - from: "server/app.py route handlers"
      to: "requireSessionUser"
      via: "userId = requireSessionUser(userId), placed after the field checks and before getMongoClient()"
      pattern: "userId = requireSessionUser\\(userId\\)"
    - from: "server/app.py request_hardware"
      to: "projectsDB.requestHardwareSet"
      via: "requester name taken from the session's username"
      pattern: "session\\['username'\\]"
    - from: "client/src/api/hardware.js and client/src/api/projects.js throwForErrorResponse"
      to: "client/src/api/sessionEvents.js notifySignedOut"
      via: "called when response.status is 401, before the error is thrown"
      pattern: "notifySignedOut\\(\\)"
    - from: "client/src/App.js"
      to: "client/src/api/sessionEvents.js onSignedOut"
      via: "useEffect subscription that clears account and selectedProjectId and returns to the signIn view; unsubscribes on unmount"
      pattern: "onSignedOut\\("
---

<objective>
Fix demo step 17 ("TA joins project id with existing id. Test if authorization works."). Today every project and hardware route in server/app.py reads the acting userId from the JSON body or query string. None of them compares it to session['userId'], even though /login and /add_user already set that in a signed Flask cookie. Anyone who knows a member's userId can act as that member. This plan binds the claimed userId to the signed-in session on all 10 routes. It also teaches the client to return to the sign-in view when the server says the session is gone.

Locked decisions (from the task description; cite by ID):
- D-01: Add requireSessionUser(claimedUserId) to server/app.py. It raises NotSignedInError, which maps to 401 {"error": "not_signed_in"}, or SessionUserMismatchError, which maps to 403 {"error": "forbidden_user_mismatch"}. Both are registered through errorhandlers, the same way MissingDatabaseConfig is. It returns the session userId, and that value is what goes to the DB layer.
- D-02: Call it from all 10 routes after the existing field checks and before getMongoClient(). userId stays a required request field, and the existing missing-field 400s do not change. Order: field checks, then the session check, then membership.
- D-03: /api/hardware/request takes the requester name from session['username'] and ignores the body userName.
- D-04: /login, /add_user, /me, /logout, /healthz and static serving stay untouched. assertProjectMember's 403 not_a_project_member stays.
- D-05: The conftest api fixture becomes a client that signs in (through session_transaction) as whatever userId each request claims. It copies the claimed value as-is, so the strict xfails B1-B5 still reach the same code and the count stays exactly 17 xfailed. It never signs in on /login, /add_user, /me or /logout. Add bare_api and sign_in fixtures. Baseline: 404 passed, 17 xfailed.
- D-06: New server/tests/test_session_authorization.py covering every route: (a) no session gives 401; (b) session user differs from claimed user gives 403 with no state change; (c) acting as yourself works, and /request stores the session username; (d) a signed-in non-member gets 403 not_a_project_member. Plus a guard test that compares app.url_map against the route table, so a future route cannot skip the check.
- D-07: Update the AUTH.md paragraph that describes this gap.
- D-08: Client. New client/src/api/sessionEvents.js exports notifySignedOut and onSignedOut. api/hardware.js and api/projects.js fire it on any 401. App.js subscribes and returns to the sign-in view. Add client/src/__tests__/session-expired.test.js. Baseline client suite: 128 passed. Must pass `npm --prefix client test` and `npm --prefix client run build`.
- D-09: PR #14 just made check-in accountability per-project in server/hardwareDatabase.py. Do not change check-in semantics. This plan does not touch server/hardwareDatabase.py, server/projectsDatabase.py or server/usersDatabase.py.

Purpose: PROJ-02 (join an existing project by ID) must be authorized against the signed-in account, not a typed userId. ACCT-04's session becomes the identity every data route trusts. This closes the gap AUTH.md documents ("doesn't yet stop someone who already knows a userId from calling those other routes as them").

Output: session-bound server routes with a guard test that covers future routes, a signing test harness that keeps the 404-pass / 17-xfail baseline, and a client that returns to sign-in on 401.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.claude/CLAUDE.md
@server/app.py
@server/tests/conftest.py
@server/tests/test_api_contract.py
@AUTH.md

Interfaces the executor needs (verified during planning, do not re-derive):
- Flask is 3.0.3. FlaskClient.open(self, *args, buffered=False, follow_redirects=False, **kwargs) is what .get()/.post() funnel into. FlaskClient.session_transaction() writes the session cookie into the client's jar without calling open(). app.test_client() instantiates app.test_client_class.
- Custom-exception errorhandlers still fire with app.testing = True. The existing MissingDatabaseConfig handler proves this (test_database_not_configured_is_a_json_503 passes today).
- The mongo fixture seeds collection hardwareDB.PROJECTS_COLLECTION ("Households") with {"householdId": "H1", "users": ["alice", "bob"]}. The users collection is "Users". The hardware collection is hardwareDB.HARDWARE_SETS_COLLECTION. The DB name is hardwareDB.DB_NAME.
- Helper signatures: usersDB.addUser(client, username, userId, password); hardwareDB.createHardwareSet(client, projectId, rawName, capacity); hardwareDB.checkoutHardware(client, projectId, rawName, quantity, userId); hardwareDB.addReservation(client, projectId, rawName, quantity, userId, userName) returns (reservationId, serializedSet). The test password "correct horse battery" passes the password policy.
- Tests send userId three ways, and the signing client must read all three: json={...} on POST; query_string={...} on GET (test_api_contract._call, test_project_routes, test_hardware_set_management); and a query embedded in the URL ("/api/hardware?projectId=H1&userId=alice" in test_adversarial_hardware.py lines 304, 341, 342).
- Strict xfail bad values (test_project_routes.py _NON_STR) are {"$ne": ""}, 5, ["x"], plus "   " (whitespace). All of them survive Flask's tagged-JSON session serializer unchanged, so copying them as-is into the session keeps B1-B5 on the same code path.
- test_api_contract.test_database_not_configured_is_a_json_503 builds its own plain test client and sends no session. Once the session check precedes getMongoClient(), it would get 401 instead of 503 unless it signs in first.
- test_type_validation.test_request_rejects_dict_userName_and_writes_nothing sends userName {"$ne": "nope"} and expects 400. It keeps passing only if the signing client copies a body userName into session['username'] as-is (see Task 1).
- Client tests use Vitest + Testing Library with vi.stubGlobal('fetch', ...) and a jsonResponse(status, body) helper (see client/src/__tests__/api.test.js). app.test.js mocks ../api/auth.js. MyProjectsPage calls getUserProjects on mount and renders an "Open" button per project. components/Project.js (ResourceView) calls fetchHardware on mount.
</context>

<tasks>

<task type="tracer">
  <name>Task 1 (tracer): Bind /join_project to the session end-to-end, with the signing test harness</name>
  <files>server/app.py, server/tests/conftest.py, server/tests/test_session_authorization.py</files>
  <read_first>server/app.py (MissingDatabaseConfig + handler at lines 41-55, /login session writes at 127-128, /me at 137-145, join_project at 156-181), server/tests/conftest.py, server/tests/test_join_project.py, server/tests/test_project_routes.py lines 1-60 and 266-300 (B1-B5 markers and _NON_STR)</read_first>
  <action>
Wire ONE route, /join_project (the demo step 17 route), through the whole session path: signed cookie, then the session guard, then the errorhandler JSON, then the DB layer. Convert the test harness so the full existing suite still passes.

server/app.py, per D-01:
- Next to MissingDatabaseConfig, define two Exception subclasses, NotSignedInError and SessionUserMismatchError. Give each a docstring stating its HTTP mapping and why it is its own class: so the handler cannot swallow unrelated errors, the same rationale MissingDatabaseConfig's docstring gives.
- Register an @app.errorhandler for each. NotSignedInError returns jsonify({"error": "not_signed_in"}) with 401, the same body /me already uses. SessionUserMismatchError returns jsonify({"error": "forbidden_user_mismatch"}) with 403.
- Define requireSessionUser(claimedUserId). It reads session.get('userId') and session.get('username'). If either is missing or empty, it raises NotSignedInError. That mirrors /me's rule, and /request relies on the username being present (Task 2). If the session userId != claimedUserId, it raises SessionUserMismatchError. Otherwise it returns the session userId.
- Write a comment above the function explaining the threat (the body/query userId is caller-controlled, the session is signed with SECRET_KEY) and the ordering rule from D-02.

In join_project, per D-02: after the two existing field checks and before getMongoClient(), add the exact statement userId = requireSessionUser(userId). Do not touch any other route in this task. Leave /login, /add_user, /me and /logout byte-for-byte unchanged (D-04).

server/tests/conftest.py, per D-05:
- Add a FlaskClient subclass, for example SessionSigningClient, that overrides open().
- When the path is not one of /login, /add_user, /me or /logout, open() finds the userId the request claims. Check in this order: the json kwarg (if it is a dict), then the query_string kwarg (dict, or str/bytes parsed with urllib.parse.parse_qs), then the query part of the URL string (split on "?", parse_qs).
- If the claimed value is neither None nor "", write it as-is into session['userId'] through self.session_transaction() before delegating to super().open(). As-is means no str() coercion, so B1-B5 stay on the same path.
- In the same transaction, set session['username'] to the json body's userName value as-is when that key is present. Otherwise set it to the claimed userId value. This is a discretion choice: it models "the account that signed in under that display name". It keeps the existing request tests (stored requester "Alice") and the dict-userName type-check test in test_type_validation.py reaching the same code without editing them.
- If no userId is claimed, leave the session untouched. Those requests fail the field check with 400 first.
- Change the api fixture so it monkeypatches flask_app_module.app.test_client_class to the subclass (monkeypatch auto-reverts) and returns app.test_client(). Keep the getMongoClient monkeypatch and app.testing = True.
- Add a bare_api fixture: same getMongoClient monkeypatch, plain app.test_client(), no automatic sign-in.
- Add a sign_in fixture that returns a function sign_in(client, userId, username=None). It writes session['userId'] = userId and session['username'] = username (or userId when username is None) through client.session_transaction().
- Give every fixture a docstring saying why it exists. In particular: api simulates "each request comes from the account it names", so the pre-existing tests keep testing their own behavior. Authorization itself is tested with bare_api in test_session_authorization.py.

server/tests/test_session_authorization.py (new), per D-06:
- Build the file around a module-level ROUTES table so Task 2 only adds rows. Each row holds the HTTP method, the path, a function that builds a valid payload claiming a given userId (for a project that user belongs to), the success status code, and whether the route is membership-gated. Add one row for POST /join_project, which joins existing project H1, expects 200 and is not membership-gated.
- Add a seeded fixture: usersDB.addUser for alice ("Alice") and bob ("Bob") with the test password. H1 already lists both. Add a call helper that sends GET payloads as query_string and POST payloads as json.
- Add a snapshot helper covering the Users, hardwareDB.PROJECTS_COLLECTION and hardwareDB.HARDWARE_SETS_COLLECTION documents (minus _id, stably ordered).
- Add a forbid_db fixture that re-monkeypatches app.getMongoClient to a function that records the call and raises AssertionError. Tests (a) and (b) then prove the guard runs before any DB connection.
- Parametrize these over ROUTES:
  - (a) bare_api, no session: 401 {"error": "not_signed_in"}, snapshot unchanged, DB never opened.
  - (b) sign_in as bob, payload claims alice: 403 {"error": "forbidden_user_mismatch"}, snapshot unchanged, DB never opened.
  - (c) sign_in as alice, payload claims alice: the row's success status.
  - Field order: bare_api with no session and the userId key removed gets the route's existing missing-field 400. Each row also needs its missing-field error code: "invalid_input" for POST routes, "missing_parameter" for GET /api/hardware.
- Add two non-parametrized tests through the real cookie path:
  - Demo step 17: create project P2 owned by bob (projectsDB.createProject(mongo, "Robotics", "P2", "desc", "bob")). POST /login as alice through bare_api, then POST /join_project {"userId": "alice", "projectId": "P2"}. Expect 200 with alice now in P2's users. On the same signed-in client, POST /join_project claiming userId "bob" for P2 gets 403 forbidden_user_mismatch.
  - After POST /logout, alice's join_project call gets 401 not_signed_in.
  </action>
  <verify>
    <automated>server/venv/bin/python -m pytest -q server/tests/test_session_authorization.py server/tests/test_join_project.py server/tests/test_session.py && server/venv/bin/python -m pytest -q server 2>&1 | tail -1 | grep -E "^[0-9]+ passed, 17 xfailed"</automated>
  </verify>
  <done>/join_project returns 401 not_signed_in with no session and 403 forbidden_user_mismatch when the session user differs from the claimed userId. In both cases it writes nothing and never calls getMongoClient. It succeeds for the signed-in user, including through a real /login cookie. The full server suite reports N passed (N greater than 404) with exactly 17 xfailed and no failures.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Guard the remaining nine routes, take the requester name from the session, and lock the route table</name>
  <files>server/app.py, server/tests/test_session_authorization.py, server/tests/test_api_contract.py, AUTH.md</files>
  <read_first>server/app.py routes at lines 222-573, server/tests/test_api_contract.py (ROUTES, stocked fixture, test_database_not_configured_is_a_json_503), server/tests/test_route_smoke.py (url_map walking pattern), AUTH.md lines 29-63</read_first>
  <behavior>
    - With no session, each of the 10 ROUTES rows returns 401 not_signed_in, writes nothing and never opens the DB
    - Signed in as bob but claiming alice, each row returns 403 forbidden_user_mismatch, writes nothing and never opens the DB
    - Signed in as alice and claiming alice, each row returns its success status: join 200, list 200, create 201, info 200, GET hardware 200, checkin 200, checkout 200, request 201, release 200, rename 200, set_active 200
    - Signed in as mallory and claiming mallory (not in H1), each of the 8 membership-gated rows returns 403 not_a_project_member and writes nothing. join_project, create_project and get_user_projects_list have no membership precondition, so (d) does not apply to them
    - Signed in as alice with username "Alice", POST /api/hardware/request whose body sends userName "Mallory" returns 201, and the stored request's userName is "Alice"
    - The set of (method, rule) pairs in app.url_map, minus the exempt endpoints, equals the set of (method, path) pairs in ROUTES
  </behavior>
  <action>
Write the new rows and tests first and watch the rows for the nine unguarded routes fail (RED). Then guard the routes (GREEN).

server/tests/test_session_authorization.py, per D-06:
- Extend the seeded fixture: hardwareDB.createHardwareSet(mongo, "H1", "HWSet1", 10); hardwareDB.checkoutHardware(mongo, "H1", "HWSet1", 3, "alice") so check-in has units to return; hardwareDB.addReservation(mongo, "H1", "HWSet1", 1, "alice", "Alice") to get a requestId for /release. Expose the requestId to the payload builders, for example by passing the seeded context into each builder.
- Add rows for the nine remaining routes with payloads that succeed for alice in H1:
  - get_user_projects_list: userId only.
  - create_project: new projectId P9 with name and description.
  - get_project_info: H1.
  - GET /api/hardware: H1 as query.
  - checkin: HWSet1, quantity 1.
  - checkout: HWSet1, quantity 1.
  - request: HWSet1, quantity 1.
  - release: the seeded requestId.
  - rename: HWSet1 to a new unused name.
  - set_active: HWSet1 with active true, so the set is not deactivated while units are checked out. If that does not return 200, seed a second set with nothing checked out and deactivate that one instead.
- Mark the 8 project-scoped rows (get_project_info and the seven /api/hardware rows) as membership-gated, and add test (d) parametrized over those rows.
- Add the session-username test from the behavior list. Read the stored requester from the raw hardware-set document's reservations, or from GET /api/hardware's requests list, whichever the existing tests use.
- Add the guard test. Walk flask_app_module.app.url_map.iter_rules(). For each rule whose endpoint is not in a module-level EXEMPT_ENDPOINTS set of login, add_user, me, logout, healthz, serve_client and static, collect (method, rule.rule) for the methods in rule.methods intersected with GET and POST. Assert that this set equals the set of (method, path) pairs in ROUTES. The failure message must tell the reader to add a ROUTES row (which gets the 401/403 coverage) or justify an EXEMPT_ENDPOINTS entry.

server/app.py, per D-02:
- In get_user_projects_list, create_project (after all four of its field checks), get_project_info, get_hardware_status, checkin_hardware, checkout_hardware, request_hardware, release_hardware, rename_hardware and set_hardware_active, insert userId = requireSessionUser(userId). It goes after the route's existing field checks and before its getMongoClient() call. Use exactly that statement form, so join_project from Task 1 makes 10 occurrences.
- Do not add or reorder any field check. Do not touch the membership except-clauses (D-04).

request_hardware, per D-03:
- Stop reading the requester name from the request body. After the requireSessionUser line, set userName from session['username'] and pass it to projectsDB.requestHardwareSet with the same signature.
- Add a one-line comment: the display name comes from the signed-in account, so a caller cannot record a request under another name.
- Do not modify server/projectsDatabase.py, server/hardwareDatabase.py or server/usersDatabase.py. Check-in semantics from PR #14 stay as they are (D-09).

server/tests/test_api_contract.py:
- Add the sign_in fixture to the parameters of test_database_not_configured_is_a_json_503.
- Call sign_in(client, payload["userId"]) right after the client is built. With the session check now ahead of getMongoClient(), the test would otherwise get 401 instead of reaching the 503 path it pins.
- Update its docstring to say so. Leave every other test in the file unchanged. They run through the signing api fixture.

AUTH.md, per D-07:
- Rewrite the "What this does not cover" paragraph under "How the session actually works". It currently says the other routes trust userId with zero session check. Replace it with the enforced behavior:
  - Every project and hardware route (list the 10) requires a signed-in session.
  - The userId in the body or query must equal the session's userId. No session gives 401 {"error": "not_signed_in"}. A different userId gives 403 {"error": "forbidden_user_mismatch"}.
  - The order is field checks, then the session check, then membership.
  - /api/hardware/request records the session's username.
  - server/tests/test_session_authorization.py's guard test fails if a new route skips the check.
  - Keep one honest remaining-limits sentence: the protection is only as strong as SECRET_KEY, and without it sessions reset on restart.
- In the app.py bullet near line 35 that lists the status codes, add "no session -> 401, session/userId mismatch -> 403".
- Change nothing else in AUTH.md.
  </action>
  <verify>
    <automated>server/venv/bin/python -m pytest -q server/tests/test_session_authorization.py server/tests/test_api_contract.py && test "$(grep -v '^\s*#' server/app.py | grep -o 'userId = requireSessionUser(userId)' | wc -l)" -ge 10 && git diff --quiet 8e0c3db -- server/hardwareDatabase.py server/projectsDatabase.py server/usersDatabase.py && server/venv/bin/python -m pytest -q server 2>&1 | tail -1 | grep -E "^[0-9]+ passed, 17 xfailed"</automated>
    <human-check>With the server running and signed in as alice in a browser, POST /join_project from devtools with {"userId": "bob", "projectId": "P1"}. Expect 403 forbidden_user_mismatch. Repeat with curl and no cookie. Expect 401 not_signed_in.</human-check>
  </verify>
  <done>All 10 routes call requireSessionUser after their field checks and before getMongoClient. The (a), (b), (c) and field-order tests pass for all 10 rows, and (d) passes for the 8 membership-gated rows. /request stores the session username regardless of the body. The url_map guard passes and would fail for an unlisted route. The 503 contract test signs in and still sees database_not_configured. The AUTH.md gap paragraph describes the enforced binding. The DB modules are byte-identical to 8e0c3db. The full suite reports exactly 17 xfailed and no failures.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Client returns to the sign-in view on any 401 from the hardware or project API</name>
  <files>client/src/api/sessionEvents.js, client/src/api/hardware.js, client/src/api/projects.js, client/src/App.js, client/src/__tests__/session-expired.test.js</files>
  <read_first>client/src/App.js, client/src/api/hardware.js, client/src/api/projects.js, client/src/__tests__/app.test.js (auth.js mocking + beforeEach), client/src/__tests__/api.test.js (fetch stub + jsonResponse), client/src/pages/MyProjectsPage.js lines 30-120, client/src/components/Project.js lines 30-60</read_first>
  <behavior>
    - onSignedOut(listener) registers the listener and returns an unsubscribe function. notifySignedOut() calls every registered listener. After unsubscribe, the listener is not called
    - fetchHardware, and a POST helper such as checkoutHardware, on a 401 {"error": "not_signed_in"} reject with message "not_signed_in" AND call the signed-out listener exactly once
    - getUserProjects and joinProject on a 401 reject with "not_signed_in" AND call the listener
    - A 403 (not_a_project_member or forbidden_user_mismatch) and a 409 still reject as before and do NOT call the listener
    - App, with getCurrentSession resolving {username: "Alice", userId: "alice"}, the real MyProjectsPage and api/projects.js, and fetch for /get_user_projects_list answering 401 not_signed_in: the "Sign in" heading appears and "Signed in as Alice" disappears
    - App, with /get_user_projects_list answering 200 and one project P1: clicking "Open" mounts the real ResourceView. fetch for /api/hardware answers 401 not_signed_in, and the "Sign in" heading appears. Signing in again lands on the project picker, not on P1
  </behavior>
  <action>
Per D-08, write client/src/__tests__/session-expired.test.js first (RED). Then implement.

client/src/__tests__/session-expired.test.js:
- Mock only ../api/auth.js, as app.test.js does, with getCurrentSession resolving the Alice session and signOut resolving {}.
- Stub fetch with a URL-keyed implementation and a jsonResponse helper.
- Use the real MyProjectsPage, components/Project.js, api/projects.js and api/hardware.js, so the App tests run the whole chain: page, API module, sessionEvents, App.
- Call vi.unstubAllGlobals in afterEach. Unsubscribe any listener a unit test registers directly.

client/src/api/sessionEvents.js (new):
- Keep a module-level Set of listeners.
- Export onSignedOut(listener): adds the listener and returns a function that removes it.
- Export notifySignedOut(): iterates over a copy of the set, so a listener that unsubscribes during the call is safe, and calls each listener.
- Add a JSDoc block on each export. A file-header comment explains why it exists: the API modules have no access to React state, so they announce "the server says you are signed out" and App.js decides what to show.

client/src/api/hardware.js and client/src/api/projects.js:
- Import notifySignedOut.
- In each module's existing throwForErrorResponse, call notifySignedOut() when response.status is 401, before building and throwing the error. The thrown error keeps its current message and fields, so callers' own catch blocks behave as before.
- Do not change client/src/api/auth.js. Its 401s are expected outcomes: invalid_credentials on sign-in, and the boot-time /me check.

client/src/App.js:
- Factor the local-state reset in handleSignOut (setAccount(null), setAuthView('signIn'), setSelectedProjectId(null)) into a clearSignedInState function. handleSignOut keeps calling signOut() first, then clearSignedInState.
- Add a useEffect with an empty dependency array that returns onSignedOut(clearSignedInState), so it unsubscribes on unmount.
- Do not call signOut() from the 401 path: the server already has no session.
- Add a short comment tying it to demo step 17 / D-08: a 401 means the session cookie is gone or expired, so the user returns to sign-in instead of seeing a raw not_signed_in error.
- Change no other rendering. Do not add a notice banner, because the decision is only "returns to the sign-in view".
  </action>
  <verify>
    <automated>npm --prefix client test -- session-expired && npm --prefix client test && npm --prefix client run build</automated>
    <human-check>In the running app, sign in and open a project. Delete the session cookie in devtools and click Check Out. Expect the sign-in form to appear.</human-check>
  </verify>
  <done>session-expired.test.js passes. The full client suite passes, with 128 baseline tests plus the new ones, and no regressions in app.test.js, api.test.js or projects.test.js. The production build succeeds. A 401 from any hardware or project call returns the app to the sign-in view. Other error statuses behave exactly as before.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| browser -> Flask API (JSON body / query string) | userId, userName, projectId and every other field are caller-controlled and untrusted |
| browser -> Flask API (session cookie) | Signed with SECRET_KEY (itsdangerous). Trusted for identity only after signature verification |
| server -> client (401 response) | The client treats a 401 from data routes as "signed out". Only the server's response drives this |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-gfz-01 | Spoofing | All 10 project/hardware routes in server/app.py (body/query userId) | high | mitigate | requireSessionUser compares the claimed userId with session['userId']. No session gives 401 not_signed_in; a different userId gives 403 forbidden_user_mismatch. The session value is what reaches the DB layer (Tasks 1-2, D-01/D-02). Proven by the (a)/(b) parametrized tests over all 10 rows plus the real /login demo-step-17 test |
| T-gfz-02 | Spoofing / Repudiation | POST /api/hardware/request requester name | medium | mitigate | The requester name comes from session['username'], and the body userName is ignored (Task 2, D-03). A test sends body userName "Mallory" while signed in as Alice and asserts "Alice" is stored |
| T-gfz-03 | Elevation of Privilege | Future routes added to server/app.py | medium | mitigate | The url_map guard test in test_session_authorization.py fails unless every non-exempt route has a ROUTES row, which brings it under the 401/403 tests (Task 2, D-06) |
| T-gfz-04 | Tampering | Flask session cookie | medium | accept | Existing control: the cookie is signed with SECRET_KEY and httpOnly, so it cannot be forged or read by JS. Residual: if SECRET_KEY is unset, the random per-process key only resets sessions on restart and does not weaken signing. AUTH.md states this (Task 2) |
| T-gfz-05 | Tampering | Cross-site request forgery on session-authorized POSTs | low | accept | The routes read bodies with request.get_json(silent=True), which needs a JSON content type. A cross-site form cannot send that without a CORS preflight, and the app configures no CORS. Before this plan these routes had no authentication at all, so the change strictly narrows exposure |
| T-gfz-06 | Information Disclosure | Status-code ordering (400 before 401/403) | low | accept | Field checks run before the session check (D-02), which reveals only the route's required field names. These are already public in AUTH.md. The mismatch 403 tells the caller nothing beyond their own session identity |
| T-gfz-07 | Denial of Service | Client signed-out listener | low | accept | Only a 401 from the hardware/project modules triggers it. auth.js 401s (bad credentials, boot /me) do not. The worst case is returning to the sign-in form, which is the correct state for a 401 |
| T-gfz-SC | Tampering | npm/pip/cargo installs | low | accept | No packages are installed or upgraded. The plan uses Flask's built-in session/test client, the existing pytest/mongomock dev deps, and the existing Vitest/Testing Library devDependencies |
</threat_model>

<verification>
- `server/venv/bin/python -m pytest -q server` exits 0 and its last line matches "N passed, 17 xfailed" with N > 404. The strict xfail count is unchanged per D-05.
- `grep -v '^\s*#' server/app.py | grep -n 'userId = requireSessionUser(userId)'` lists one line inside each of the 10 route functions. The match count is at least 10. The exact per-route coverage is pinned by the parametrized 401/403 tests and the url_map guard.
- `git diff --quiet 8e0c3db -- server/hardwareDatabase.py server/projectsDatabase.py server/usersDatabase.py` exits 0 (D-09).
- server/tests/test_session.py and server/tests/test_auth_routes.py pass unchanged. /login, /add_user, /me and /logout are untouched (D-04).
- `npm --prefix client test` passes (128 baseline plus new) and `npm --prefix client run build` succeeds.
</verification>

<success_criteria>
- Demo step 17: a TA signed in as themselves can join an existing project ID. Typing another member's userId into any project or hardware request is refused with 403. A request with no session is refused with 401.
- Every one of the 10 routes is session-bound, and the guard test makes sure the next route will be too.
- The 404-pass / 17-xfail server baseline holds, plus the new tests. The client suite and build pass.
- AUTH.md no longer documents the trust-the-userId gap as open.
</success_criteria>

<output>
Create `.planning/quick/261109-gfz-demo-step-17-bind-api-routes-to-the-sess/261109-gfz-SUMMARY.md` when done
</output>
