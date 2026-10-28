<p align="center"><img src="app/static/logo.svg" width="96" alt="Portarr"></p>

# Portarr

**Français** · [English](README.en.md)

Petit outil web pour **exporter et importer la configuration de Radarr, Sonarr, Lidarr, Whisparr et Prowlarr** : formats personnalisés, profils de qualité, tailles par qualité, nommage, profils de métadonnées (Lidarr), et côté Prowlarr les profils de synchronisation, indexeurs et proxys d'indexeurs. Pensé pour appliquer les [guides TRaSH](https://trash-guides.info/Radarr/) ou répliquer une configuration d'une instance à une autre, sans tout refaire à la main.

## Ce que ça fait

| Application | Élément | Remarque |
|---|---|---|
| Radarr, Sonarr, Lidarr, Whisparr | Formats personnalisés | Import direct des JSON de TRaSH-Guides (un objet ou une liste) |
| Radarr, Sonarr, Lidarr, Whisparr | Profils de qualité | Scores, groupes de qualités, cutoff, langue (Radarr, Whisparr v3), tailles propres à chaque qualité d'un profil (Whisparr v2, hors groupes) |
| Lidarr | Profils de métadonnées | Types d'albums (principaux et secondaires) et statuts de sortie autorisés |
| Radarr, Sonarr, Lidarr, Whisparr | Tailles par qualité | min / préféré / max |
| Radarr, Sonarr, Lidarr, Whisparr | Nommage | |
| Radarr, Sonarr, Lidarr, Whisparr | Gestion des médias | Décoché par défaut ; les réglages propres à l'hôte (corbeille, permissions) sont exclus |
| Prowlarr | Profils de synchronisation | |
| Prowlarr | Indexeurs | Priorité, profil, tags, réglages. **Sans les secrets** (voir ci-dessous) |
| Prowlarr | Proxys d'indexeurs | FlareSolverr, etc. Sans les secrets |

Points clés :

- **Indépendant des identifiants.** Tout est référencé par *nom* (formats dans les scores, qualités, cutoff, tags, profils de synchronisation). Un export d'une instance s'importe sur une autre où les IDs sont différents. Les tags manquants sont créés sur la cible.
- **Aperçu obligatoire.** Chaque import affiche d'abord ce qui sera créé / modifié / ignoré, avec le détail champ par champ, et vous décochez ce que vous ne voulez pas.
- **Sauvegarde automatique.** L'état de la cible est enregistré dans `/config/backups` juste avant toute écriture. Si la sauvegarde échoue, rien n'est modifié.
- **Rien n'est jamais supprimé** sur la cible.
- **Une application vers la même application** uniquement (Sonarr → Sonarr, Lidarr → Lidarr…) : un export est refusé sur une autre application.
- Les clés API de vos instances restent côté serveur et ne sont jamais renvoyées au navigateur.

Compatible Radarr v4+/v5+, Sonarr v4+ et Whisparr v2 / v3 « Eros » (API v3), Lidarr et Prowlarr (API v1). Le type d'application est détecté automatiquement à l'ajout d'une instance. Interface en français ou anglais selon le navigateur, thème clair / sombre / automatique.

### Les secrets des indexeurs

Prowlarr masque les clés API, mots de passe et noms d'utilisateur dans son API : ils **ne peuvent pas être exportés**, et Portarr ne les met jamais dans un fichier (le fichier peut donc être partagé sans risque). Conséquences à l'import :

- un indexeur **nouveau** qui en a besoin est créé **désactivé** (sans test de connexion, qui échouerait) : renseignez ses secrets sur la cible puis activez-le ;
- un indexeur **existant** conserve ses secrets, et son état activé / désactivé n'est pas modifié s'il en a ;
- les indexeurs publics, sans secret, sont créés normalement.

Les *Applications* (liens Prowlarr → Radarr/Sonarr, qui contiennent des clés API) et les clients de téléchargement ne sont volontairement pas gérés : ils dépendent de votre environnement.

> Lidarr et Prowlarr ont été validés contre une simulation fidèle à leur spécification OpenAPI officielle, Whisparr contre une simulation fondée sur son code source (il ne publie pas de spécification) ; aucun n'a encore été essayé sur une vraie instance. Utilisez toujours l'aperçu d'abord, la sauvegarde automatique couvre le reste.

## Installation avec Docker

Portarr tourne dans un seul conteneur, sans base de données : tout ce qu'il retient (vos instances et les sauvegardes) tient dans le volume `/config`. Le conteneur s'exécute avec l'utilisateur **568:568** (celui de TrueNAS), donc ce volume doit être inscriptible par lui.

### Avec Docker Compose (le plus simple)

```bash
git clone https://github.com/ali0cha/portarr.git
```

```bash
cd portarr && mkdir -p config && sudo chown 568:568 config
```

```bash
docker compose up -d --build
```

L'image est construite localement, sans registre. Ouvrez ensuite `http://localhost:8765`. Pour mettre à jour : `git pull`, puis relancez la dernière commande.

### Avec `docker run`

```bash
docker run -d --name portarr --restart unless-stopped -p 8765:8765 -v portarr-config:/config ghcr.io/ali0cha/portarr:latest
```

Un volume nommé comme `portarr-config` convient sans réglage de droits. Avec un dossier de l'hôte (`-v /chemin/config:/config`), faites d'abord `sudo chown 568:568 /chemin/config`. Pour mettre à jour : `docker pull ghcr.io/ali0cha/portarr:latest`, puis supprimez et recréez le conteneur (le volume est conservé).

### Réglages utiles

- **Authentification** : ajoutez `-e AUTH_USER=admin -e AUTH_PASSWORD=...` (ou les mêmes clés sous `environment:` dans `docker-compose.yml`). Recommandé dès que le port n'est pas réservé à un réseau de confiance.
- **Port** : changez le premier nombre de `-p 8765:8765` (ou de `ports:` dans le compose).
- **Joindre vos instances** : indiquez une adresse que le conteneur peut atteindre, soit l'IP de l'hôte et le port de l'application (`http://192.168.1.10:7878`), soit, si Portarr et vos applications partagent un même réseau Docker, le nom du conteneur (`http://radarr:7878`). `localhost` désigne le conteneur Portarr lui-même, pas votre machine.
- **Santé** : le conteneur déclare un healthcheck (`docker ps` affiche `healthy`).

## Installation sur TrueNAS SCALE (24.10 ou plus récent)

### 1. Obtenir l'image Docker

TrueNAS tire l'image depuis un registre. Le plus simple : GitHub construit et publie l'image pour vous (cette même image sert pour `docker run` ci-dessus).

1. Créez un dépôt GitHub et poussez ce dossier sur la branche `main`.
2. L'onglet **Actions** lance `build` : tests, puis publication de `ghcr.io/<votre-utilisateur>/portarr:latest` (amd64 et arm64).
3. Sur GitHub : profil → **Packages** → `portarr` → *Package settings* → visibilité **Public** (sinon TrueNAS devra s'authentifier pour tirer l'image).

### 2. Créer le dossier de configuration

Portarr tourne sous l'utilisateur **`apps` (uid 568)** et doit pouvoir écrire dans `/config`, sinon l'ajout d'une instance échoue (erreur 500, `PermissionError: … /config/instances.tmp` dans le journal).

1. **Datasets** → choisissez votre pool → **Add Dataset**, nom `portarr` (réglages par défaut).
2. Sélectionnez ce dataset → carte **Permissions** → **Edit** : utilisateur `apps`, groupe `apps`, cochez *Apply User* et *Apply Group*, puis enregistrez. Si l'éditeur d'ACL s'ouvre à la place, donnez à `apps` le contrôle total.
3. Dans l'application, *Storage* → **Host Path** : chemin `/mnt/<pool>/portarr`, monté sur `/config`.

### 3. Installer l'application

**Apps → Discover Apps → ⋮ (en haut à droite) → Install via YAML**, puis collez [`deploy/truenas-app.yaml`](deploy/truenas-app.yaml) en adaptant :

```yaml
services:
  portarr:
    image: ghcr.io/ali0cha/portarr:latest
    restart: unless-stopped
    user: "568:568"
    ports:
      - "30290:8765"          # port libre ≥ 9000
    environment:
      TZ: Europe/Brussels
      AUTH_USER: admin        # optionnel mais recommandé
      AUTH_PASSWORD: change-me
    volumes:
      - /mnt/VOTRE_POOL/portarr:/config
```

Ouvrez ensuite `http://<ip-truenas>:30290`.

> Sans dépôt GitHub : `docker build -t portarr:local .` depuis le shell TrueNAS puis `image: portarr:local` dans le YAML. Cette voie n'a pas été testée sur TrueNAS.

### 4. Ajouter vos instances

Onglet **Instances** → *Ajouter*. Utilisez l'adresse que le conteneur peut atteindre, typiquement `http://<ip-truenas>:<port de l'app>` (par défaut 30025 pour Radarr, 30027 pour Sonarr sur TrueNAS ; les ports par défaut hors TrueNAS sont 8686 pour Lidarr, 6969 pour Whisparr, 9696 pour Prowlarr), et la clé API de *Paramètres → Général → Sécurité*. Si vous utilisez une « URL Base », ajoutez-la (`http://…:7878/radarr`).

## Utilisation

- **Appliquer un guide TRaSH** : sur la page du guide, copiez le JSON d'un format personnalisé → onglet **Import** → *Fichier / JSON collé* → choisissez l'instance cible → **Analyser** → **Appliquer**.
- **Copier une configuration d'une instance à une autre** : onglet **Import** → *Une autre instance* → source + cible → **Analyser**. Cocher un profil coche aussi ce dont il dépend (formats notés, profil de synchronisation d'un indexeur).
- **Archiver / partager** : onglet **Export** → choisir l'instance → **Charger** → cocher → **Télécharger**.
- **Revenir en arrière** : onglet **Sauvegardes**, puis réimportez le fichier voulu avec « écraser » activé (les éléments créés entre-temps ne sont pas supprimés).

« Écraser les éléments existants » concerne les éléments appariés par nom : formats personnalisés, profils de qualité, profils de synchronisation, indexeurs, proxys. Les tailles, le nommage et la gestion des médias sont toujours mis à jour s'ils sont cochés.

## Sécurité

L'outil détient les clés API de vos instances. Gardez-le sur votre réseau local et définissez `AUTH_USER` / `AUTH_PASSWORD` (authentification HTTP basique) dès que le port est accessible depuis autre chose qu'un réseau de confiance ; ne l'exposez pas directement sur Internet (placez-le derrière un reverse proxy HTTPS si besoin). `/healthz` reste public.

## Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `PORT` | `8765` | Port d'écoute dans le conteneur |
| `CONFIG_DIR` | `/config` | Instances (`instances.json`, mode 600) et `backups/` |
| `AUTH_USER`, `AUTH_PASSWORD` | vides | Active l'authentification si les deux sont définies |

## Format du fichier d'export

JSON lisible, versionné (`"format": "portarr"`, `"version": 1`). Les profils référencent les formats et qualités par nom :

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

## Identité visuelle

L'interface reprend la structure de la dernière version de Sonarr (en-tête coloré, barre latérale, barre d'outils icône + libellé, cartes, police Inter, jeu de couleurs OKLCH clair / sombre). Chaque application de la suite [Servarr](https://wiki.servarr.com/) a sa teinte : Sonarr cyan, Radarr jaune, Lidarr vert, Readarr rouge sombre, Prowlarr orange, Whisparr rose. **Portarr prend le violet**, la teinte restée libre ; les badges d'instance gardent la couleur de leur application. Le logo est dans [`app/static/logo.svg`](app/static/logo.svg).

La police Inter (licence SIL OFL, voir `app/static/fonts/LICENSE-Inter.txt`) est embarquée : aucune ressource externe n'est chargée.

## Développement

```bash
./run_tests.sh                                   # tests dans un conteneur Python jetable
python -m tests.fake_arr radarr-a:7001 radarr-b:7002 sonarr-a:7003 sonarr-b:7004 lidarr-a:7005 lidarr-b:7006 whisparr-a:7007 whisparr-b:7008 prowlarr-a:7009 prowlarr-b:7010
                                                 # faux serveurs de démonstration (clé « demo-key »), un « -a » rempli et un « -b » cible par application
CONFIG_DIR=./config python -m app                # l'application sur http://localhost:8765
```

Le backend est du FastAPI (`app/`), le frontend du JavaScript sans étape de build (`app/static/`). `tests/fake_arr.py` simule en mémoire l'API de Radarr, Sonarr, Whisparr et Lidarr (noms uniques, cutoff valide, IDs de formats, profils de métadonnées) et de Prowlarr (secrets masqués, validation à l'enregistrement, `forceSave`). Les tests couvrent notamment l'aller-retour entre deux instances aux IDs différents, l'idempotence d'un second import et l'absence de secrets dans les exports.

## Pistes d'évolution

Import des *profils* au format TRaSH (seuls les formats personnalisés sont convertis pour l'instant), profils de délai, release profiles (Sonarr, Lidarr), Readarr, synchronisation avec suppression, traduction des messages renvoyés par le serveur.
