<p align="center"><img src="app/static/logo.svg" width="96" alt="Portarr"></p>

# Portarr

[Français](README.md) · **English**

A small web tool to **export and import the configuration of Radarr, Sonarr, Lidarr, Whisparr and Prowlarr**: custom formats, quality profiles, quality sizes, naming, metadata profiles (Lidarr), and for Prowlarr sync profiles, indexers and indexer proxies. Built to apply the [TRaSH Guides](https://trash-guides.info/Radarr/) or to replicate a setup from one instance to another without redoing everything by hand.

## What it does

| Application | Item | Notes |
|---|---|---|
| Radarr, Sonarr, Lidarr, Whisparr | Custom formats | Direct import of TRaSH Guides JSON (one object or a list) |
| Radarr, Sonarr, Lidarr, Whisparr | Quality profiles | Scores, quality groups, cutoff, language (Radarr, Whisparr v3), per-quality size limits inside a profile (Whisparr v2, groups excluded) |
| Lidarr | Metadata profiles | Allowed album types (primary and secondary) and release statuses |
| Radarr, Sonarr, Lidarr, Whisparr | Quality sizes | min / preferred / max |
| Radarr, Sonarr, Lidarr, Whisparr | Naming | |
| Radarr, Sonarr, Lidarr, Whisparr | Media management | Unchecked by default; host-specific settings (recycle bin, permissions) are excluded |
| Prowlarr | Sync profiles | |
| Prowlarr | Indexers | Priority, profile, tags, settings. **Without secrets** (see below) |
| Prowlarr | Indexer proxies | FlareSolverr, etc. Without secrets |

Key points:

- **Independent of IDs.** Everything is referenced by *name* (formats in scores, qualities, cutoff, tags, sync profiles). An export from one instance imports into another where the IDs differ. Missing tags are created on the target.
- **Preview first, always.** Every import shows what will be created / updated / skipped, field by field, and you untick whatever you don't want.
- **Automatic backup.** The target's current state is saved in `/config/backups` right before anything is written. If the backup fails, nothing is changed.
- **Nothing is ever deleted** on the target.
- **Same application to same application** only (Sonarr → Sonarr, Lidarr → Lidarr…): an export is refused on a different application.
- Your instances' API keys stay on the server and are never sent back to the browser.

Works with Radarr v4+/v5+, Sonarr v4+ and Whisparr v2 / v3 "Eros" (API v3), Lidarr and Prowlarr (API v1). The application type is detected automatically when you add an instance. The interface is in French or English depending on your browser, with a light / dark / automatic theme.

### Indexer secrets

Prowlarr masks API keys, passwords and usernames in its API: they **cannot be exported**, and Portarr never writes them to a file (so the file can be shared safely). What this means on import:

- a **new** indexer that needs them is created **disabled** (without a connection test, which would fail): fill in its secrets on the target, then enable it;
- an **existing** indexer keeps its secrets, and its enabled / disabled state is left untouched if it has any;
- public indexers, which have no secrets, are created normally.

*Applications* (Prowlarr → Radarr/Sonarr links, which contain API keys) and download clients are deliberately not handled: they depend on your environment.

> Lidarr and Prowlarr were validated against a simulation faithful to their official OpenAPI specification, Whisparr against a simulation based on its source code (it does not publish a specification); none has been tried on a real instance yet. Always use the preview first; the automatic backup covers the rest.

## Installing with Docker

Portarr runs in a single container with no database: everything it remembers (your instances and the backups) lives in the `/config` volume. The container runs as user **568:568** (the TrueNAS one), so that volume must be writable by it.

### With Docker Compose (simplest)

```bash
git clone https://github.com/ali0cha/portarr.git
```

```bash
cd portarr && mkdir -p config && sudo chown 568:568 config
```

```bash
docker compose up -d --build
```

The image is built locally, no registry needed. Then open `http://localhost:8765`. To update: `git pull`, then run the last command again.

### With `docker run`

```bash
docker run -d --name portarr --restart unless-stopped -p 8765:8765 -v portarr-config:/config ghcr.io/ali0cha/portarr:latest
```

A named volume such as `portarr-config` works without any permission tweaks. With a host folder (`-v /path/config:/config`), first run `sudo chown 568:568 /path/config`. To update: `docker pull ghcr.io/ali0cha/portarr:latest`, then remove and recreate the container (the volume is kept).

### Useful settings

- **Authentication**: add `-e AUTH_USER=admin -e AUTH_PASSWORD=...` (or the same keys under `environment:` in `docker-compose.yml`). Recommended whenever the port is not limited to a trusted network.
- **Port**: change the first number in `-p 8765:8765` (or in `ports:` in the compose file).
- **Reaching your instances**: give an address the container can reach: either the host's IP and the application's port (`http://192.168.1.10:7878`), or, if Portarr and your applications share a Docker network, the container name (`http://radarr:7878`). `localhost` means the Portarr container itself, not your machine.
- **Health**: the container declares a healthcheck (`docker ps` shows `healthy`).

## Installing on TrueNAS SCALE (24.10 or newer)

### 1. Get the Docker image

TrueNAS pulls the image from a registry. Simplest: GitHub builds and publishes it for you (the same image is used by `docker run` above).

1. Create a GitHub repository and push this folder to the `main` branch.
2. The **Actions** tab runs `build`: tests, then publishing `ghcr.io/<your-user>/portarr:latest` (amd64 and arm64).
3. On GitHub: your profile → **Packages** → `portarr` → *Package settings* → visibility **Public** (otherwise TrueNAS will have to authenticate to pull the image).

### 2. Create the configuration folder

Portarr runs as user **`apps` (uid 568)** and must be able to write to `/config`, otherwise adding an instance fails (error 500, `PermissionError: … /config/instances.tmp` in the log).

1. **Datasets** → pick your pool → **Add Dataset**, name `portarr` (default settings).
2. Select that dataset → **Permissions** card → **Edit**: user `apps`, group `apps`, tick *Apply User* and *Apply Group*, then save. If the ACL editor opens instead, give `apps` full control.
3. In the app, *Storage* → **Host Path**: path `/mnt/<pool>/portarr`, mounted on `/config`.

### 3. Install the app

**Apps → Discover Apps → ⋮ (top right) → Install via YAML**, then paste [`deploy/truenas-app.yaml`](deploy/truenas-app.yaml), adjusting:

```yaml
services:
  portarr:
    image: ghcr.io/ali0cha/portarr:latest
    restart: unless-stopped
    user: "568:568"
    ports:
      - "30290:8765"          # a free port ≥ 9000
    environment:
      TZ: Europe/Brussels
      AUTH_USER: admin        # optional but recommended
      AUTH_PASSWORD: change-me
    volumes:
      - /mnt/YOUR_POOL/portarr:/config
```

Then open `http://<truenas-ip>:30290`.

> Without a GitHub repository: run `docker build -t portarr:local .` from the TrueNAS shell, then use `image: portarr:local` in the YAML. This route has not been tested on TrueNAS.

### 4. Add your instances

**Instances** tab → *Add*. Use the address the container can reach, typically `http://<truenas-ip>:<app port>` (30025 for Radarr and 30027 for Sonarr by default on TrueNAS; outside TrueNAS the default ports are 8686 for Lidarr, 6969 for Whisparr, 9696 for Prowlarr), and the API key from *Settings → General → Security*. If you use a "URL Base", include it (`http://…:7878/radarr`).

## Usage

- **Apply a TRaSH guide**: on the guide's page, copy the JSON of a custom format → **Import** tab → *File / pasted JSON* → pick the target instance → **Analyse** → **Apply**.
- **Copy a setup from one instance to another**: **Import** tab → *Another instance* → source + target → **Analyse**. Ticking a profile also ticks what it depends on (scored formats, an indexer's sync profile).
- **Archive / share**: **Export** tab → pick the instance → **Load** → tick → **Download**.
- **Roll back**: **Backups** tab, then re-import the file you want with "overwrite" enabled (items created in the meantime are not deleted).

"Overwrite existing items" applies to items matched by name: custom formats, quality profiles, sync profiles, indexers, proxies. Sizes, naming and media management are always updated when ticked.

## Security

The tool holds your instances' API keys. Keep it on your local network and set `AUTH_USER` / `AUTH_PASSWORD` (HTTP basic authentication) as soon as the port is reachable from anything other than a trusted network; do not expose it directly to the Internet (put it behind an HTTPS reverse proxy if needed). `/healthz` stays public.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8765` | Listening port inside the container |
| `CONFIG_DIR` | `/config` | Instances (`instances.json`, mode 600) and `backups/` |
| `AUTH_USER`, `AUTH_PASSWORD` | empty | Enables authentication when both are set |

## Export file format

Readable, versioned JSON (`"format": "portarr"`, `"version": 1`). Profiles reference formats and qualities by name:

```json
{
  "qualityProfiles": [{
    "name": "HD Bluray + WEB",
    "cutoff": "WEB 1080p",
    "items": [{"name": "WEB 1080p", "allowed": true, "items": ["WEBDL-1080p", "WEBRip-1080p"]}],
    "formatItems": [{"name": "x265 (HD)", "score": -10000}]
  }]
}
```

## Visual identity

The interface follows the structure of the latest Sonarr (coloured page header, sidebar, icon + label toolbar, cards, Inter font, light / dark OKLCH colour scheme). Each application in the [Servarr](https://wiki.servarr.com/) family has its own hue: Sonarr cyan, Radarr yellow, Lidarr green, Readarr dark red, Prowlarr orange, Whisparr pink. **Portarr takes violet**, the hue left free; instance badges keep their application's colour. The logo is in [`app/static/logo.svg`](app/static/logo.svg).

The Inter font (SIL OFL licence, see `app/static/fonts/LICENSE-Inter.txt`) is bundled: no external resource is loaded.

## Development

```bash
./run_tests.sh                                   # tests in a throwaway Python container
python -m tests.fake_arr radarr-a:7001 radarr-b:7002 sonarr-a:7003 sonarr-b:7004 lidarr-a:7005 lidarr-b:7006 whisparr-a:7007 whisparr-b:7008 prowlarr-a:7009 prowlarr-b:7010
                                                 # demo fake servers (key "demo-key"): a populated "-a" and a target "-b" per application
CONFIG_DIR=./config python -m app                # the app on http://localhost:8765
```

The backend is FastAPI (`app/`), the frontend is build-free JavaScript (`app/static/`). `tests/fake_arr.py` simulates the Radarr, Sonarr, Whisparr and Lidarr APIs in memory (unique names, valid cutoff, format IDs, metadata profiles) and Prowlarr's (masked secrets, validation on save, `forceSave`). The tests cover in particular the round trip between two instances with different IDs, the idempotence of a second import, and the absence of secrets in exports.

## Ideas for later

Import of quality *profiles* in TRaSH format (only custom formats are converted for now), delay profiles, release profiles (Sonarr, Lidarr), Readarr, sync with deletion, translation of the messages returned by the server.
