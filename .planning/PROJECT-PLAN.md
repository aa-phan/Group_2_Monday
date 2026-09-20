# PantryTrack — Project Plan (R1-1)

**Team:** Group 2 Monday · MIS385N Team Project, Fall 2026
**Project:** PantryTrack, a household food inventory web app (Proof of Concept)
**Last updated:** 2026-09-20

## 1. Team Members

| Name | Track | Responsibility |
|------|-------|----------------|
| Siddharth Kolukuluri | A. Account & Household Management | Sign-up and sign-in, credential encryption, sessions, creating and joining households |
| Aaron Phan | B. Inventory Management | Inventory by location, restock, reserve, consume, freshness flags |
| Kody Keo | C. Data Integration & API | REST API, live MongoDB data with no hard-coded values, password reset, custom storage locations |
| Aashrith Attelli | D. Deployment & Quality | PyTest coverage, cloud deployment, architecture sketch |

## 2. Methodology

The team follows an Agile approach built around user stories.
- Work is written as user stories of three sentences or less, plus technical-debt and research items.
- Work is split into one-week sprints.
- Features are built on short-lived branches and merged through pull requests. [Proposed: at least one teammate reviews each PR before it merges to `main`.]
- Bugs and improvements are tracked as GitHub Issues, separate from the story board.

## 3. Sprint Cadence

| Activity | When | Where |
|----------|------|-------|
| Sprint review and planning | Every Monday, at the lab meeting | EER 0.818 |
| Midweek check-in | Every Thursday | Discord |

- Sprint length: 1 week, Monday to Monday.
- Sprint 1 starts 2026-09-21. Checkpoint 1 is due 2026-09-21 at 10:00 AM.

**Velocity:** measured as user stories completed per one-week sprint. No sprint has been completed yet, so the baseline will be recorded after Sprint 1 and used to plan later sprints.

## 4. Collaboration Tools

| Purpose | Tool |
|---------|------|
| Communication and check-ins | Discord |
| Source code | GitHub repository (Dr. Samant and the TAs have access) |
| User-story board | GitHub Projects board "PantryTrack" (To do, In progress, Done) |
| Bug and improvement tracking | GitHub Issues, kept separate from the story board |
| Code review | GitHub pull requests |

## 5. Toolchain

| Layer | Tool |
|-------|------|
| Front end | React (built with Vite) |
| Back end | Python and Flask, exposing a REST API |
| Database | MongoDB [Atlas] |
| Testing | PyTest |
| Version control | Git and GitHub |
| Hosting | [cloud host] |
| Passwords | Hashed (for example bcrypt), never stored in plaintext |

The reasoning behind these choices is covered in the tech stack and approach write-up (see section 6).

## 6. Checkpoint 1 Deliverables

| Rubric item | Story | Owner |
|-------------|-------|-------|
| R1-1 Project Plan | As the instructor, I want a documented project plan covering team members, sprint cadence, collaboration tools, implementation methodology, and toolchain so I can assess how the team is organized and working together. | Siddharth Kolukuluri (Track A) |
| R1-2 Feature board | As the instructor, I want to see every planned feature captured as user stories, technical debt, or research items on a shared board so I can verify the team has scoped its work before implementation begins. | Aaron Phan (Track B) |
| R1-3 High-level sketch | As the instructor, I want a high-level sketch of the application's architecture and user flow so I can quickly understand the system's design before reviewing the code. | Aashrith Attelli (Track D) |
| Supporting: tech stack and approach | As the instructor, I want a written explanation of the team's chosen tech stack and technical approach so I can evaluate whether the decisions fit the project's needs. | Kody Keo (Track C) |
