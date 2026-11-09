---
phase: 261109-gee-demo-step-10-show-app-insufficient-stock
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - client/src/components/QuantityAction.js
  - client/src/components/CheckOut.js
  - client/src/__tests__/checkout-over-available.test.js
  - client/src/__tests__/components.test.js
autonomous: true
requirements:
  - RES-04

estimate:
  tokens: 30000
  raw_tokens: 30000
  tasks: 2
  confidence: low

must_haves:
  truths:
    - "When a user types a Check Out quantity above the set's available count and clicks Check Out, the request reaches POST /api/hardware/checkout. No browser constraint-validation tooltip blocks it."
    - "The server's 409 insufficient_stock reply appears as the app's own alert under the Check Out control, reading \"Only N available -- can't check out M.\""
    - "Check Out stays disabled when available is 0 and when the hardware set is deactivated"
    - "Check In is unchanged: its quantity input still carries max={checkedOut} and CheckIn.js is not modified"
    - "The full client Vitest suite passes and the production build succeeds"
  artifacts:
    - path: "client/src/components/QuantityAction.js"
      provides: "Optional capInput prop (default true) that controls whether max goes on the input as a native constraint, separate from the max-below-1 disable logic"
      contains: "capInput"
    - path: "client/src/components/CheckOut.js"
      provides: "Check Out opts out of the native input cap while keeping max={available} for disabling"
      contains: "capInput={false}"
    - path: "client/src/__tests__/checkout-over-available.test.js"
      provides: "End-to-end client test: HardwareSet -> CheckOut -> QuantityAction -> real api/hardware.js -> stubbed fetch 409 -> alert text"
      contains: "insufficient_stock"
    - path: "client/src/__tests__/components.test.js"
      provides: "Updated Check Out cap assertions plus unit coverage of the capInput contract"
      contains: "capInput"
  key_links:
    - from: "client/src/components/CheckOut.js"
      to: "client/src/components/QuantityAction.js"
      via: "capInput={false} alongside max={available} and disabled={disabled}"
      pattern: "capInput=\\{false\\}"
    - from: "client/src/components/QuantityAction.js"
      to: "the rendered number input"
      via: "max attribute set only when capInput is true; nothingToDo still derived from max"
      pattern: "capInput \\? max"
    - from: "client/src/api/hardware.js throwForErrorResponse (error.onHand / error.requested)"
      to: "client/src/components/CheckOut.js describeCheckoutError"
      via: "409 body fields carried onto the thrown Error, then formatted into the alert"
      pattern: "Only \\$\\{error.onHand\\} available"
---

<objective>
Fix demo step 10 ("Try checking out more than available"). Today an over-available Check Out quantity never leaves the browser. `QuantityAction` renders `<input type="number" max={max}>` and `CheckOut` passes `max={available}`, so the browser's native HTML5 constraint validation cancels the submit and shows its own tooltip. The server already rejects the request with 409 `insufficient_stock` plus `onHand`/`requested` (server/app.py checkout route). client/src/api/hardware.js already carries those fields onto the thrown error, and CheckOut's `describeCheckoutError` already formats them. The only missing link is letting the submit happen.

Purpose: RES-04 says the checkout "is rejected if it would exceed what's currently available". The demo must show that rejection as the app's own message, "Only N available -- can't check out M.", driven by live server data, not as a browser tooltip.

Output: an optional `capInput` prop on QuantityAction (default true, so CheckIn and every other caller keep today's behavior). CheckOut passes `capInput={false}`. A new end-to-end client test proves the full path, and the unit tests pin the prop contract.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.claude/CLAUDE.md
@client/src/components/QuantityAction.js
@client/src/components/CheckOut.js
@client/src/components/CheckIn.js
@client/src/components/HardwareSet.js
@client/src/api/hardware.js
@client/src/__tests__/components.test.js
@client/src/__tests__/api.test.js

<interfaces>
Current contracts the executor needs (extracted, do not re-read to confirm):

- QuantityAction props: label, busyLabel, action(quantity:number) async and throws on failure, describeError(error) returns string, onChanged() async, max (optional number), disabled (optional boolean, default false). Internal: nothingToDo = disabled || (typeof max === 'number' && max < 1). Input attributes today: type="number" min="1" max={max} step="1" disabled={nothingToDo}. The button is disabled when busy || nothingToDo. The submit handler calls event.preventDefault(), runs action(Number(quantity)) then awaits onChanged(), and on throw sets the alert text from describeError.
- CheckOut props: projectId, userId, hwSetName, available, onChanged, disabled. Renders QuantityAction with label "Check Out", busyLabel "Checking out...", max={available}, disabled={disabled}.
- describeCheckoutError(error): returns the hardware_set_inactive message, else "Only ${error.onHand} available -- can't check out ${error.requested}." when typeof error.onHand === 'number', else the quantity-field message, else error.message.
- HardwareSet renders CheckOut with available={hwSet.available} and disabled={inactive} (inactive = hwSet.active === false). It also renders CheckIn with checkedOut={hwSet.myCheckedOut} and HardwareSetAdmin, which makes no API call on mount.
- api/hardware.js checkoutHardware(payload) POSTs JSON to '/api/hardware/checkout' with headers Content-Type application/json. A non-ok response throws Error(body.error) with onHand/requested/checkedOut/field copied when present.
- Server 409 body for over-checkout: {"error": "insufficient_stock", "onHand": <int>, "requested": <int>}.
- jsdom 30.1.2 (the test env) enforces constraint validation in requestSubmit. A submit-button click on a form whose input has value 9 and max="2" is cancelled before the submit event fires. That is why the new end-to-end test is a genuine RED before the fix.
- Test runner: Vitest 3 + Testing Library + user-event. Config is in client/vite.config.js (environment jsdom, setupFiles ./src/test/setup.js, which registers jest-dom and cleanup). The fetch-stub pattern from api.test.js: vi.stubGlobal('fetch', vi.fn()) in beforeEach, vi.unstubAllGlobals() in afterEach, and jsonResponse(status, body) returning { ok, status, json: async () => body }.
- Baseline: npm --prefix client test reports 121 passed. components.test.js reports 42 passed.
</interfaces>
</context>

<tasks>

<task type="tracer" tdd="true">
  <name>Task 1: End-to-end over-available Check Out reaches the server and shows the app's insufficient-stock alert</name>
  <files>client/src/__tests__/checkout-over-available.test.js, client/src/components/QuantityAction.js, client/src/components/CheckOut.js, client/src/__tests__/components.test.js</files>
  <read_first>client/src/components/QuantityAction.js, client/src/components/CheckOut.js, client/src/__tests__/api.test.js (lines 1-25 for the fetch-stub pattern), client/src/__tests__/components.test.js (lines 157-223 CheckOut block and 330-341 HardwareSet cap test)</read_first>
  <behavior>
    - Render HardwareSet (projectId "P1", userId "alice", onChanged a vi.fn resolving undefined) with hwSet {hwSetName "HWSet1", capacity 10, available 2, myCheckedOut 0, active true}. Global fetch is stubbed to resolve jsonResponse(409, {error "insufficient_stock", onHand 2, requested 9}). Clear the "Check Out" input, type 9, and click the "Check Out" button. Expect:
      - fetch called exactly once with URL '/api/hardware/checkout' and method POST.
      - The parsed JSON body equals {projectId "P1", userId "alice", hwSetName "HWSet1", quantity 9}.
      - findByRole('alert') has text "Only 2 available -- can't check out 9."
      - onChanged not called, and the Check Out button is enabled again afterwards.
    - RED proof before the fix: this test fails. jsdom's constraint validation (input max="2") cancels the submit, so fetch is never called.
    - After the fix, the existing CheckOut and HardwareSet assertions that pinned max="4" / max="2" on the Check Out input are updated to assert the attribute is absent. The Check In assertions (max "5" at about line 288, max "3" at about line 339) stay exactly as they are.
  </behavior>
  <action>
    Implements RES-04 (demo step 10). Approach follows the orchestrator's suggestion of a prop on QuantityAction, not noValidate on the form (Claude's discretion). A prop removes only the max constraint. The native min="1" and step="1" checks keep their current behavior for zero and fractional quantities, and Check In is untouched.

    1. RED. Create client/src/__tests__/checkout-over-available.test.js. Do NOT vi.mock '../api/hardware.js': the point is to exercise the real checkoutHardware and throwForErrorResponse. Copy the jsonResponse helper and the stubGlobal/unstubAllGlobals beforeEach/afterEach pattern from api.test.js. Import HardwareSet from '../components/HardwareSet.js', and render, screen, waitFor from '@testing-library/react' plus userEvent. Write one test per the behavior block. Read the request with fetch.mock.calls[0]: assert the first arg is '/api/hardware/checkout', options.method is 'POST', and JSON.parse(options.body) deep-equals the expected payload. Run the file and confirm it fails because fetch was not called. Commit as test(261109-gee): add failing end-to-end test for over-available checkout.

    2. GREEN, QuantityAction. In client/src/components/QuantityAction.js add an optional boolean prop capInput, destructured with default true. Render the input's max attribute as capInput ? max : undefined, so the attribute is omitted when capInput is false. Leave nothingToDo computed from max exactly as now. max below 1 must still disable the input and the button, and disabled must still disable both, whatever capInput is. Do not add noValidate to the form, and do not touch min, step, the submit handler, or the error/busy logic. JSDoc changes:
       - Extend the max param doc: max always drives the max-below-1 disable, but only goes on the input as a native constraint when capInput is true.
       - Add a capInput param doc: optional, default true. False means a quantity above max is still submitted, so the server's rejection message is shown instead of the browser's constraint tooltip.
       Keep the change additive (one prop, one attribute expression, docs). A separate in-flight task is changing Check In behavior and may touch this file, so a small diff keeps any merge trivial.

    3. GREEN, CheckOut. In client/src/components/CheckOut.js pass capInput={false} to QuantityAction. Keep max={available} and disabled={disabled} as they are, so Check Out still disables at available 0 and while the set is deactivated. Leave describeCheckoutError unchanged; it already formats onHand/requested. Update the component JSDoc and the available param doc. available disables Check Out at 0, but it is deliberately not a native input cap: an over-request goes to the server, which answers 409 insufficient_stock, and that answer is shown as "Only N available -- can't check out M." (demo step 10, RES-04).

    4. Do NOT modify client/src/components/CheckIn.js. Check In behavior belongs to a separate task. CheckIn keeps the default capInput, so its max={checkedOut} attribute is unchanged.

    5. Fix the two existing assertions in client/src/__tests__/components.test.js that encode the old Check Out cap:
       - In the CheckOut describe block, rename the test 'caps the quantity input at the units available, not a fixed number' to 'does not put available on the input as a native max, so an over-request reaches the server', and change its assertion to expect(screen.getByLabelText('Check Out')).not.toHaveAttribute('max').
       - In the HardwareSet test "caps Check In at myCheckedOut (this user's own holding), not capacity - available", change only the Check Out line to not.toHaveAttribute('max'). Leave the Check In line toHaveAttribute('max', '3') exactly as is, and adjust the test's comment if it mentions the Check Out cap.

    6. Run the full client suite. Commit as feat(261109-gee): let over-available Check Out reach the server and show insufficient-stock message.
  </action>
  <verify>
    <automated>npm --prefix client test -- src/__tests__/checkout-over-available.test.js && npm --prefix client test</automated>
    <human-check>With the app running against live MongoDB, open a project and pick a hardware set showing Available 2 (or any N greater than 0). Type a larger number (for example 9) in Check Out and click Check Out. Expected: no browser tooltip appears, a red alert under Check Out reads "Only 2 available -- can't check out 9.", and Available is unchanged. A set with Available 0, or a deactivated set, still shows Check Out disabled.</human-check>
  </verify>
  <acceptance_criteria>
    - The new test failed before steps 2-3 (recorded in the test commit) and passes after them.
    - grep -c "capInput={false}" client/src/components/CheckOut.js prints 1.
    - grep -c "capInput" client/src/components/QuantityAction.js prints 3 or more (JSDoc, destructure, max expression).
    - npm --prefix client test passes with 122 or more tests (121 baseline plus the new end-to-end test) and no failures.
    - git diff --name-only for this task's commits does not list client/src/components/CheckIn.js.
  </acceptance_criteria>
  <done>An over-available Check Out quantity is POSTed to /api/hardware/checkout, and the 409 reply shows "Only N available -- can't check out M." as the app's alert. Check Out still disables at available 0 and when deactivated. Check In's max attribute is unchanged. The full client suite is green, and the work is committed as a test commit followed by a feat commit.</done>
</task>

<task type="auto">
  <name>Task 2: Pin the capInput contract with unit tests so the Check In work can't silently regress Check Out</name>
  <files>client/src/__tests__/components.test.js</files>
  <read_first>client/src/__tests__/components.test.js (lines 47-155 QuantityAction block, 157-223 CheckOut block)</read_first>
  <action>
    Regression guards for the Task 1 behavior (RES-04). The parallel Check In task may edit QuantityAction.js, so the Check Out contract needs pinning at unit level, independent of the end-to-end test. Add tests only, using the existing setup() helper, the mocked checkoutHardware, and the props fixture already in components.test.js. Do not change production code in this task. If a new test fails, fix QuantityAction.js or CheckOut.js per the Task 1 contract and note it in the summary.

    In the QuantityAction describe block, add:
    - 'omits the native max but keeps min and step when capInput is false': setup({ max: 5, capInput: false }). Expect the input to have no max attribute, min '1', and step '1'.
    - 'submits a quantity above max when capInput is false': setup({ max: 2, capInput: false }). Clear the input, type 9, and click "Do It". Expect action called with 9 (typeof number).
    - 'still disables at max below 1 when capInput is false': setup({ max: 0, capInput: false }). Expect the input and button disabled.
    - 'still honors disabled when capInput is false': setup({ max: 5, capInput: false, disabled: true }). Expect the input and button disabled.
    Keep the existing 'caps the input at max when given' test unchanged. It now also proves the default capInput is true.

    In the CheckOut describe block, add:
    - 'sends an over-available quantity to the server and shows how many are available': checkoutHardware.mockRejectedValue of an Error('insufficient_stock') with onHand 2 and requested 9 assigned. Render CheckOut with available 2, then clear, type 9, and click Check Out. Expect checkoutHardware called with { projectId 'P1', userId 'alice', hwSetName 'HWSet1', quantity 9 }, and the alert text "Only 2 available -- can't check out 9."
    - Extend the existing 'disables checkout when nothing is available' test to also assert the Check Out input is disabled.
    - 'disables checkout while the set is deactivated even with units available': render CheckOut with available 5 and disabled. Expect the button and input disabled.

    Then run the full suite and the production build. Commit as test(261109-gee): pin capInput contract for Check Out.
  </action>
  <verify>
    <automated>npm --prefix client test -- src/__tests__/components.test.js && npm --prefix client test && npm --prefix client run build</automated>
  </verify>
  <acceptance_criteria>
    - grep -c "capInput: false" client/src/__tests__/components.test.js prints 4 or more.
    - components.test.js reports 48 or more passing tests (42 baseline plus 6 new), with no failures.
    - The full client suite passes and npm --prefix client run build exits 0.
    - The Check In describe block and its max assertions are unchanged (git diff shows no edits inside the describe('CheckIn') block).
  </acceptance_criteria>
  <done>Unit tests pin that capInput={false} omits only the native max and still disables at max below 1 or when disabled. They also pin that the default keeps the cap, and that CheckOut sends over-available quantities to the server and renders the insufficient-stock message. The suite and build are green and committed.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| browser -> Flask API (/api/hardware/checkout) | The quantity is user-controlled input. Removing the client-side max means larger quantities now cross this boundary |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-fq2-01 | Tampering | CheckOut quantity input (client max removed) | low | accept | The client cap was never a security control, since any HTTP client can bypass it. The server stays authoritative: projectsDB.checkoutHardwareSet raises InsufficientStockError, which maps to 409 insufficient_stock (server/app.py), and server/tests/test_checkout.py covers it. min="1"/step="1" native checks and the server's invalid_input 400 still reject zero, negative, and fractional quantities |
| T-fq2-02 | Information Disclosure | 409 body onHand/requested shown in the alert | low | accept | onHand is the same available count already rendered on the card for this project member. Nothing new is exposed |
| T-fq2-03 | Denial of Service | Repeated over-available submits | low | accept | Each submit is one request, and the button disables while busy (existing QuantityAction busy state). Load is no different from today's valid checkouts |
| T-fq2-SC | Tampering | npm/pip/cargo installs | low | accept | No packages are installed or upgraded. The plan uses only the existing Vitest/Testing Library devDependencies in client/package.json |
</threat_model>

<verification>
- npm --prefix client test passes: the full suite plus the new checkout-over-available.test.js.
- npm --prefix client run build exits 0.
- An over-available Check Out in the running app shows the app's red alert, not a browser tooltip (human-check, end-of-phase).
- CheckIn.js is untouched, and the Check In max assertions in components.test.js are unchanged.
</verification>

<success_criteria>
- Demo step 10 works. Typing a quantity above Available and clicking Check Out produces "Only N available -- can't check out M." from the live server's 409, and Available does not change.
- Check Out remains disabled at Available 0 and for deactivated sets.
- Check In behavior and code are unchanged.
- Three atomic commits: the failing e2e test, the feat fix, and the unit-test hardening.
</success_criteria>

<output>
Create `.planning/quick/261109-gee-demo-step-10-show-app-insufficient-stock/261109-gee-SUMMARY.md` when done
</output>
