# Security Testing Guide

This guide defines practical security testing for the Employee Dialogue Flask app.

## Scope

The checks below cover:
- dependency vulnerabilities,
- static code security scanning,
- authentication and authorization behavior,
- workflow transition tampering,
- input handling checks.

## 1. Local Security Scan Commands

Run from repo root with the virtual environment active.

```bash
uv sync --extra dev
uvx uv-secure uv.lock
uv run bandit -r src/employee_dialogue
uv run pytest -v
```

## 2. CI Security Scans

GitHub Actions workflow `.github/workflows/security.yml` runs:
- `uv-secure` for vulnerable dependencies,
- `bandit` static analysis.

## 3. Manual Security Test Checklist

### Authentication and access control
- Verify unauthenticated users are redirected from protected routes.
- Verify users cannot edit/delete entries owned by other users.
- Verify only the manager can access manager finalize/edit routes.
- Verify only the designated program manager can approve.

### Workflow tampering
- Try direct POST to `/entries/<id>/submit` when status is not finalized.
- Try direct POST to `/entries/<id>/approve` when status is not submitted.
- Confirm state does not change on blocked transitions.

### Input handling
- Submit long text over configured limits and verify rejection.
- Submit HTML/JS payloads in text fields and verify output is safely escaped.
- Confirm multiline text rendering remains readable in summaries and email body.

### Operational checks
- Ensure `ALLOW_FINALIZED_DELETE_TESTING` is disabled outside test environments.
- Ensure `SECRET_KEY` is strong and unique per environment.
- Rotate and protect SMTP and Azure secrets.

## 4. Security Test Cases in Pytest

Repository tests include security-related coverage for:
- route authz and role checks,
- workflow transition enforcement,
- comment/goals max-length validation.

Run them with:

```bash
uv run pytest -v tests/test_app.py
```
