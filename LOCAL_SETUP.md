# Running 706 Pool Play Locally (Docker)

This runs the whole stack — Postgres, the FastAPI backend, and the React
frontend — in containers via `docker compose`. No local Python/Node install
required.

## 1. One-time setup

macOS doesn't ship a container runtime, and Docker Desktop isn't installed on
this machine, so we use [Colima](https://github.com/abiosoft/colima) (a
lightweight Docker daemon) plus the `docker` CLI.

```bash
brew install colima docker docker-compose
```

Register the `docker-compose` plugin so `docker compose` (the CLI subcommand)
can find it:

```bash
mkdir -p ~/.docker
python3 -c "
import json, pathlib
path = pathlib.Path.home() / '.docker/config.json'
cfg = json.loads(path.read_text()) if path.exists() else {}
cfg.setdefault('cliPluginsExtraDirs', [])
if '/usr/local/lib/docker/cli-plugins' not in cfg['cliPluginsExtraDirs']:
    cfg['cliPluginsExtraDirs'].append('/usr/local/lib/docker/cli-plugins')
path.write_text(json.dumps(cfg, indent=2))
"
```

You only need to do this section once per machine.

## 2. Start the Docker daemon (Colima)

```bash
colima start --cpu 2 --memory 4 --disk 20
```

First run downloads a VM image, so it takes a minute or two. Subsequent
starts are much faster.

Verify it's up:

```bash
docker info --format 'OK: {{.ServerVersion}}'
docker compose version
```

Colima doesn't restart automatically after a reboot unless you run it as a
background service:

```bash
brew services start colima
```

## 3. Build and run the app

From the repo root:

```bash
docker compose up --build
```

Or detached (runs in the background):

```bash
docker compose up --build -d
```

This starts three containers:

| Service    | URL                          | Notes                          |
|------------|-------------------------------|---------------------------------|
| frontend   | http://localhost:3000        | React app, calls backend directly |
| backend    | http://localhost:8000        | FastAPI, seeds golfer data on first boot |
| postgres   | localhost:5432               | Data persisted in a named Docker volume |

## 4. Verify it's working

```bash
curl http://localhost:8000/api/health      # {"status":"ok"}
curl http://localhost:8000/api/settings    # tournament settings
curl http://localhost:8000/api/golfers     # seeded golfer field
```

Then open http://localhost:3000 in a browser.

## 5. Everyday commands

```bash
docker compose ps                 # container status
docker compose logs -f backend    # tail logs for one service (or: frontend, postgres)
docker compose down               # stop and remove containers (Postgres data is kept)
docker compose down -v            # stop and also wipe the Postgres volume (fresh DB next start)
docker compose up --build         # rebuild after changing code/dependencies
```

## 6. Troubleshooting

**`docker: command not found` / `Cannot connect to the Docker daemon`**
Colima isn't running. Run `colima start`.

**Port already in use (3000, 8000, or 5432)**
Something else on your machine is bound to that port. Stop it, or edit the
`ports:` mapping in `docker-compose.yml` (format is `"host:container"`).

**Backend can't connect to Postgres**
Make sure the `postgres` container is healthy first:
`docker compose ps` should show `postgres` as `healthy` before `backend`
starts — compose waits for this automatically via a healthcheck.

**Stale build after a dependency change**
`docker compose up --build` should pick up changes to `requirements.txt` or
`package.json` automatically. If something still looks cached, force a clean
rebuild:
```bash
docker compose build --no-cache
```

**Start over with a clean database**
```bash
docker compose down -v
docker compose up --build
```
