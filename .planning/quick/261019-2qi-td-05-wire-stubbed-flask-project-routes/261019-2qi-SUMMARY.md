---
phase: quick-261019-2qi
plan: 01
status: complete
requirements: [DATA-02, PROJ-01, PROJ-02, PROJ-03]
completed: 2026-10-19
---

# Quick 261019-2qi: Wire stubbed Flask project routes (TD-05) Summary

Five stubbed routes (GET /main, POST /create_project, /join_project, /get_user_projects_list, /get_project_info) now run on live Mongo logic. New projects are stored under `householdId` in `Households`, so the existing `/api/hardware` membership guard accepts them.

## Commits
- 64c225d: DB modules (projectsDB: queryProject, createProject, addUser, listProjectsForUser; usersDB: getUser, joinProject, getUserProjectsList) + test_project_database.py
- see git log for the routes commit: app.py routes + test_project_routes.py

## Tests
Full backend suite: `311 passed in 25.73s` (with `--cov`, total coverage 96.48%, floor 85%).

## Deviations
- Task 2 tests were written before the routes but I did not run a separate RED pass before implementing them (Task 1 RED was confirmed: 20 failed).
- The plan file existed only in the main checkout (untracked), so it was read from there.
- Test deps were installed from server/requirements*.txt into a venv in the scratchpad (no pytest on system Python).

## Known Stubs
None.
