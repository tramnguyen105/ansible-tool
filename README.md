# Ansible Automation Console

Ansible Automation Console is an internal enterprise web application for on-premises Ansible-based network automation. It provides:

- LDAP-authenticated access for administrators
- Inventory, credentials, templates, and playbook management
- Audited job execution and scheduling
- A Cisco IOS / IOS-XE CLI-to-Ansible converter
- A Vue-based operator console designed for day-to-day network automation workflows

The codebase is intentionally structured as a modular monolith for MVP speed while keeping future expansion straightforward.

## Technology Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Celery, Redis, ansible-runner
- Frontend: Vue 3, Vite, Pinia, Vue Router, Tailwind CSS, Monaco Editor
- Database: PostgreSQL
- Directory/Auth: LDAP via `ldap3`
- Deployment: Nginx + systemd on a VM

## Repository Layout

```text
backend/                FastAPI app, Celery worker, Alembic, tests
frontend/               Vue 3 operator console
deploy/systemd/         Example systemd units
deploy/nginx/           Example Nginx site config
docs/                   Architecture notes
```

## Deployment Model

- No containers
- Linux VM recommended for production
- Nginx terminates TLS and serves the SPA
- Uvicorn runs the FastAPI app behind Nginx
- Celery worker and Celery beat run as separate systemd services
- PostgreSQL and Redis run on the same VM or internal infrastructure tier

## Backend Setup

1. Install system packages:

```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip redis-server nginx
```

2. Create a service user and directories:

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin ansibletool
sudo mkdir -p /opt/ansible-tool /var/lib/ansible-tool /var/log/ansible-tool
sudo chown -R ansibletool:ansibletool /opt/ansible-tool /var/lib/ansible-tool /var/log/ansible-tool
```

3. Copy the repository to `/opt/ansible-tool`, then create the Python virtual environment:

```bash
cd /opt/ansible-tool
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ./backend
```

4. Create the backend environment file from [`backend/.env.example`](/c:/ansible-tool/backend/.env.example):

```bash
sudo mkdir -p /etc/ansible-tool
sudo cp /opt/ansible-tool/backend/.env.example /etc/ansible-tool/backend.env
sudo chown root:ansibletool /etc/ansible-tool/backend.env
sudo chmod 640 /etc/ansible-tool/backend.env
```

5. Generate a real Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

6. Run database migrations:

```bash
cd /opt/ansible-tool/backend
source ../.venv/bin/activate
alembic upgrade head
```

7. Start the backend locally for validation:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Frontend Setup

1. Install Node.js 20+.
2. Build the SPA:

```bash
cd /opt/ansible-tool/frontend
npm install
npm run build
```

3. Copy [`frontend/.env.example`](/c:/ansible-tool/frontend/.env.example) to `frontend/.env` and adjust the API base URL if needed.

## Production Services

Example systemd units are provided in:

- [`deploy/systemd/ansible-tool-backend.service`](/c:/ansible-tool/deploy/systemd/ansible-tool-backend.service)
- [`deploy/systemd/ansible-tool-celery-worker.service`](/c:/ansible-tool/deploy/systemd/ansible-tool-celery-worker.service)
- [`deploy/systemd/ansible-tool-celery-beat.service`](/c:/ansible-tool/deploy/systemd/ansible-tool-celery-beat.service)

Enable them after copying to `/etc/systemd/system`:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ansible-tool-backend
sudo systemctl enable --now ansible-tool-celery-worker
sudo systemctl enable --now ansible-tool-celery-beat
```

## Nginx

Use the example site in [`deploy/nginx/ansible-tool.conf`](/c:/ansible-tool/deploy/nginx/ansible-tool.conf) as a starting point. The config assumes:

- frontend build output at `/opt/ansible-tool/frontend/dist`
- backend at `127.0.0.1:8000`
- TLS certificates managed separately

## Security Defaults

- LDAP is the default authentication mode
- Local admin auth is available only for bootstrap/dev and should be disabled in production
- Session cookies are HttpOnly and CSRF-protected
- Secrets are encrypted at rest with Fernet
- Audit events are recorded for authentication, playbook edits, credential usage, and job execution

## MVP Scope Choices

- Roles are admin-only for now, but the schema supports future RBAC expansion
- CSV/Excel import expects host-centric rows with `name` or `host`, optional `address`, optional `groups`, and remaining columns treated as host variables
- Scheduling uses Celery beat plus a database polling task every minute instead of dynamic beat schedule mutation
