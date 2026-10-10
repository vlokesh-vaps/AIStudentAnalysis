# AI Student Performance Analyzer

A full-stack Flask application for parsing class performance reports (CSV, XLSX, XLS, PDF) and generating AI-assisted class insights and student recommendations using Groq LLMs.

The application is fully deployment-aware and runs without code modifications in:
- **Local development** (`http://127.0.0.1:<PORT>/`, `http://localhost:<PORT>/`)
- **LAN network access** (`http://<LAN-IP>:<PORT>/`)
- **Production HTTP** (`http://<DOMAIN>/`)
- **Production HTTPS** (`https://<DOMAIN>/` or custom ports e.g. `https://<DOMAIN>:8054/`)
- **Reverse-proxy with URL prefix** (e.g. `https://<DOMAIN>:8054/student-analysis/`)
- **Docker & Docker Compose** (locally, LAN, or behind Nginx)

---

## Supported Deployment Environments

| Environment | Example URL | Configuration (.env) |
|---|---|---|
| **Local Dev** | `http://localhost:8051/` | `HOST=0.0.0.0`, `PORT=8051`, `APPLICATION_ROOT=` |
| **LAN Access** | `http://192.168.1.100:8051/` | `HOST=0.0.0.0`, `PORT=8051`, `APPLICATION_ROOT=` |
| **Production HTTP** | `http://school.example.com/` | `HOST=0.0.0.0`, `PORT=8051`, `APPLICATION_ROOT=`, `TRUSTED_PROXIES=1` |
| **Production HTTPS** | `https://school.example.com/` | `HOST=0.0.0.0`, `PORT=8051`, `APPLICATION_ROOT=`, `TRUSTED_PROXIES=1` |
| **Reverse-Proxy Prefix** | `https://school.example.com:8054/student-analysis/` | `APPLICATION_ROOT=/student-analysis`, `TRUSTED_PROXIES=1` |
| **Docker Compose** | `http://localhost:8051/` or behind Nginx | `docker compose up -d` |

---

## Local Setup

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your Groq API key to `.env`:
```env
GROQ_API_KEY=your_key_here
```

Start the application:
```powershell
python app.py
```
Or with Flask CLI:
```powershell
flask --app app run --host 0.0.0.0 --port 8051
```

Access:
- Web UI: [http://localhost:8051](http://localhost:8051)
- Swagger API Docs: [http://localhost:8051/swagger](http://localhost:8051/swagger)
- Health Check: [http://localhost:8051/api/health](http://localhost:8051/api/health)

---

## Docker Deployment

### 1. Build and Run Standalone Container
```powershell
# Build image
docker build -t ai-student-analysis .

# Run container mapping port 8051
docker run -d --name ai-student-analysis -p 8051:8051 --env-file .env ai-student-analysis

# Inspect health status
docker inspect --format='{{json .State.Health}}' ai-student-analysis

# Restart container
docker restart ai-student-analysis
```

### 2. Using Docker Compose
```powershell
# Start container in background
docker compose up -d --build

# View container logs
docker compose logs -f

# Check health
docker compose ps

# Stop container
docker compose down
```

---

## Reverse-Proxy Deployment (Nginx)

The application includes `deploy/nginx/nginx.conf` demonstrating configuration for both root domain hosting and subpath prefix hosting.

### Reverse-Proxy under a Prefix (`https://<DOMAIN>:8054/student-analysis/`)

1. Set `.env` on the backend container / server:
```env
APPLICATION_ROOT=/student-analysis
TRUSTED_PROXIES=1
TRUST_PROXY_HEADERS=true
```

2. Add location block to Nginx:
```nginx
location = /student-analysis {
    return 308 https://$http_host/student-analysis/;
}

location /student-analysis/ {
    proxy_pass http://127.0.0.1:8051;
    client_max_body_size 25M;

    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $http_host;
    proxy_set_header X-Forwarded-Port $server_port;
    proxy_set_header X-Forwarded-Prefix /student-analysis;

    proxy_connect_timeout 60s;
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

3. Validate and reload Nginx:
```bash
nginx -t
nginx -s reload
```

---

## Configuration Reference (.env)

| Variable | Default | Description |
|---|---|---|
| `FLASK_ENV` | `development` | `development` or `production` |
| `HOST` | `0.0.0.0` | Bind address (`0.0.0.0` enables LAN/Docker access) |
| `PORT` | `8051` | Listening port |
| `GROQ_API_KEY` | `""` | API key for Groq AI inference |
| `APPLICATION_ROOT` | `""` | Public path prefix (e.g. `/student-analysis`) |
| `TRUST_PROXY_HEADERS` | `true` | Enable Werkzeug ProxyFix middleware |
| `TRUSTED_PROXIES` | `1` | Number of trusted upstream proxies |
| `CORS_ORIGINS` | `*` | Allowed CORS origins or comma-separated list |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum upload size in megabytes |
| `ENABLE_DOCS` | `true` | Toggle Swagger UI at `/swagger` |
| `LOG_LEVEL` | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Running Automated Tests

Run the complete test suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Tests validate:
- Root and URL prefix page loading
- Static CSS and JavaScript asset resolution
- Trailing slash normalization and canonical redirects
- API routes (`/api/upload`, `/api/analyze/class`, `/api/analyze/student`, `/api/health`)
- Multipart file upload parsing and size limit enforcement (413)
- HTTPS scheme preservation behind reverse proxies
- Swagger documentation availability and toggle
