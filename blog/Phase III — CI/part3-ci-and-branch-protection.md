# Building a Production-Grade AI Agent from Scratch - Phase III Part 3: CI and Branch Protection

Phase III added merge-time guardrails so quality checks are automatic.

## What changed

- Added GitHub Actions workflow: `.github/workflows/ci.yml`
- Job `test-and-lint` runs on:
  - pull requests
  - pushes to `main` / `master`
  - manual trigger (`workflow_dispatch`)
- Pipeline steps:
  1. Python 3.11 setup
  2. dependency install
  3. `ruff` critical checks (`E9,F63,F7,F82`)
  4. focused test run:
     - `tests/test_auth_security.py`
     - `tests/test_session_memory.py`
     - `tests/test_redis_debug.py`

We also aligned local test execution by updating `Makefile` to run `pytest tests/ -v`.

## Branch protection note

Branch protection is configured in GitHub repository settings (not in code), so it should be enabled there to require `test-and-lint` and review approval before merging to `main`.

## Why this matters

This moves quality from "best effort" to "enforced by default," while keeping CI fast and focused on the riskiest paths.

## Files touched

- `.github/workflows/ci.yml`
- `Makefile`
