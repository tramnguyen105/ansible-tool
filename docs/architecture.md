# Architecture Summary

## Pattern

The application uses a modular monolith:

- a single FastAPI deployment unit
- a single Celery worker deployment unit
- clear domain modules under `backend/app/modules`
- shared infrastructure in `backend/app/core`, `backend/app/db`, and `backend/app/models`

## Backend Modules

- `auth`: LDAP login, server-side sessions, CSRF validation
- `users`: user record lifecycle and future RBAC expansion points
- `audit`: immutable audit trail
- `inventory`: inventory CRUD, import normalization, variables
- `credentials`: encrypted SSH credentials
- `templates`: Jinja2 template storage
- `playbooks`: YAML playbook storage and revisions
- `cli_converter`: deterministic Cisco config parser and generators
- `jobs`: ansible-runner execution, result capture
- `schedules`: cron-based job scheduling

## Runtime Flow

1. User authenticates via LDAP.
2. FastAPI creates a DB-backed session and CSRF token.
3. GUI requests backend APIs with the session cookie.
4. Long-running jobs are pushed to Celery.
5. Celery uses ansible-runner and writes result metadata back to PostgreSQL.
6. Nginx serves the frontend and proxies API traffic to FastAPI.

## Future Expansion

- RBAC can expand from the current admin-only role model
- Additional device parsers can plug into `cli_converter`
- Job approvals and multi-step workflow can layer onto the existing audit and scheduling models
