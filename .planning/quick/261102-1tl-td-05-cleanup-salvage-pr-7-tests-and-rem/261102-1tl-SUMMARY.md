# Quick Task 261102-1tl: TD-05 cleanup Summary

Removed the dead `/main` route and three projectsDatabase stubs, and ported PR #7's project tests onto main (91 collected, 17 strict xfails documenting five real bugs, none fixed).

## Commits
- 025fc96: chore: remove /main, updateUsage, checkOutHW, checkInHW; README updated
- 663e62b: test: server/tests/test_project_database.py (20 collected: 19 passed, 1 xfailed)
- d7cd3e6: test: server/tests/test_project_routes.py (71 collected: 55 passed, 16 xfailed)

## Results
- Full suite: 361 passed, 17 xfailed, 0 XPASS.
- Coverage (server/.coveragerc, run from server/): 97.59%, floor 85% reached. (Plan predicted 97.31%.)
- GET /main with a built client returns the SPA index; `mainPage` is not in view_functions.

## Deviations
- The bad-field matrix test seeds users alice and carol before posting (the `mongo` fixture creates no Users documents); the plan did not state this explicitly. Counts match the plan exactly.
- Environment: shared server/.venv lacks pytest-cov; installed it to a scratchpad directory (not the venv) and loaded it via sys.path.

## Found bugs (strict xfail, not fixed)
| ID | Cases | Description |
|----|-------|-------------|
| B1 | 3 | /get_user_projects_list does not catch InvalidProjectInput; non-string userId is an unhandled exception (HTTP 500) |
| B2 | 5 | Blank checks use `not value`; whitespace-only values pass validation and are persisted (/create_project x4 fields, /join_project userId) |
| B3 | 3 | /create_project reports field `creatorUserId` instead of wire name `userId` for non-string userId |
| B4 | 3 | /join_project answers 404 project_not_found on projectId for a non-string userId, though the project exists |
| B5 | 3 | create_project/join_project (route x2, DB joinProject x1) never check the Users collection, so a userId without an account becomes a member |

Total 17. B5's fix is larger than it looks: the `mongo` fixture creates no Users documents, and many existing tests act as such users.

## Dropped tests
- getUser (5 cases): test_get_user_omits_password (1) and test_get_user_returns_none_for_unknown_or_non_str (4); usersDB.getUser does not exist on main.
- /main (8 cases): test_main_returns_portal_summary_without_password, test_main_reflects_live_data, test_main_missing_user_id, test_main_unknown_user, and test_main_rejects_blank_user_id (4 params); the route is deleted.

## Notes
- PR #7 can now be closed as superseded; that is the user's call.
- `projects` on User documents is written once as [] and never read or updated: a dead field, not a defect in scope.
- Out-of-scope stale README entries (`/check_out`, `/get_hw_info`) left alone.
