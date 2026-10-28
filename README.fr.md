<p align="center"><img src="app/static/logo.svg" width="96" alt="Portarr"></p>

# Portarr

[English](README.md) · **Français**

Portarr est un petit outil web qui **exporte et importe la configuration qualité de Radarr, Sonarr, Lidarr, Whisparr et Prowlarr**. Il sert à appliquer les [TRaSH Guides](https://trash-guides.info/), copier une configuration d'une instance à une autre, ou la sauvegarder et la partager, sans tout refaire à la main.

## Fonctionnalités

| Application | Ce qu'on peut exporter et importer |
|---|---|
| Radarr, Sonarr, Lidarr, Whisparr | Formats personnalisés, profils de qualité (scores, groupes, cutoff, langue), tailles par qualité, nommage, gestion des médias |
| Radarr, Sonarr | Profils des [TRaSH Guides](https://trash-guides.info/), choisis dans le catalogue ou collés en JSON |
| Lidarr | Profils de métadonnées (types d'albums et statuts de sortie) |
| Prowlarr | Profils de synchronisation, indexeurs, proxys d'indexeurs |

- **Des noms, pas des IDs.** Formats, qualités, tags et profils sont référencés par nom : un export d'une instance s'importe sur une autre dont les IDs sont différents.
- **Aperçu d'abord.** Chaque import liste ce qui sera créé, modifié ou ignoré, champ par champ. Vous décochez ce que vous ne voulez pas.
- **Sauvegarde automatique** de la cible, faite juste avant toute écriture. Si elle échoue, rien n'est modifié.
- **Ne supprime jamais** rien sur la cible.
- **Sans risque à partager.** Les exports ne contiennent ni clé API ni mot de passe, et les clés de vos instances ne quittent jamais le serveur.
- **Une application vers la même application** uniquement : un export Sonarr est refusé sur Radarr.
- Interface en anglais et en français (sélecteur dans l'en-tête), thème clair et sombre, et le type d'application est détecté à l'ajout d'une instance.

Compatible avec Radarr v4+/v5+, Sonarr v4+, Whisparr v2 et v3 « Eros » (API v3), Lidarr et Prowlarr (API v1).

> Lidarr et Prowlarr ont été validés contre des simulations de leurs spécifications OpenAPI officielles, et Whisparr contre une simulation fondée sur son code source (il ne publie pas de spécification). Aucun n'a encore été essayé sur une vraie instance. Lisez toujours l'aperçu ; la sauvegarde automatique couvre le reste.

Remarques : la gestion des médias est décochée par défaut, et les réglages propres à l'hôte (corbeille, permissions) ne sont jamais exportés. Les tailles par qualité d'un profil de Whisparr v2 sont conservées, sauf pour les qualités d'un groupe.

## Installation

Portarr tourne dans un seul conteneur, sans base de données. Tout ce qu'il retient (vos instances, les sauvegardes, le cache TRaSH) est dans le volume `/config`, qui **doit être inscriptible par l'utilisateur `568:568`**.

L'image est construite et publiée automatiquement par les GitHub Actions de ce dépôt : `ghcr.io/ali0cha/portarr:latest` (amd64 et arm64).

### Docker Compose

```bash
git clone https://github.com/ali0cha/portarr.git && cd portarr
mkdir -p config && sudo chown 568:568 config
docker compose up -d --build
```

L'image est construite en local, sans registre. Ouvrez <http://localhost:8765>.

### docker run

```bash
docker run -d --name portarr --restart unless-stopped -p 8765:8765 -v portarr-config:/config ghcr.io/ali0cha/portarr:latest
```

Un volume nommé fonctionne sans changer aucun droit. Avec un dossier de l'hôte (`-v /chemin/config:/config`), faites d'abord `sudo chown 568:568 /chemin/config`.

Réglages utiles :

- **Authentification** : ajoutez `-e AUTH_USER=admin -e AUTH_PASSWORD=...` (ou les mêmes clés sous `environment:` dans `docker-compose.yml`). Recommandé sauf si le port est réservé à un réseau de confiance.
- **Port** : changez le premier nombre de `-p 8765:8765` (ou de `ports:` dans le compose).
- **Joindre vos instances** : utilisez une adresse que le conteneur peut atteindre, soit l'IP de l'hôte et le port de l'application (`http://192.168.1.10:7878`), soit, sur un réseau Docker commun, le nom du conteneur (`http://radarr:7878`). `localhost` désigne le conteneur Portarr lui-même.

### TrueNAS SCALE (24.10 ou plus récent)

1. **Créez le stockage.** *Datasets* → votre pool → *Add Dataset*, nommé `portarr`. Puis *Permissions* → *Edit* : utilisateur `apps`, groupe `apps`, cochez *Apply User* et *Apply Group*, enregistrez. Si l'éditeur d'ACL s'ouvre à la place, donnez à `apps` le contrôle total.
2. **Installez l'application.** *Apps → Discover Apps → ⋮ → Install via YAML*, puis collez [`deploy/truenas-app.yaml`](deploy/truenas-app.yaml) en adaptant le port et le chemin du dataset :

   ```yaml
   services:
     portarr:
       image: ghcr.io/ali0cha/portarr:latest
       restart: unless-stopped
       pull_policy: always     # retélécharge l'image à chaque enregistrement
       user: "568:568"
       ports:
         - "30290:8765"          # un port libre, 9000 ou plus
       environment:
         TZ: Europe/Brussels
         AUTH_USER: admin        # optionnel mais recommandé
         AUTH_PASSWORD: change-me
       volumes:
         - /mnt/YOUR_POOL/portarr:/config
   ```

3. **Ouvrez** `http://<ip-truenas>:30290`, puis ajoutez vos instances.

Si l'ajout d'une instance échoue avec une erreur HTTP 500 et `Permission denied: '/config/…'` dans le journal de l'application, le dossier n'est pas inscriptible par l'uid 568 : corrigez son propriétaire ou son ACL.

### Ajouter vos instances

*Instances* → *Ajouter une instance*. Indiquez l'adresse que le conteneur peut atteindre et la clé API de *Paramètres → Général → Sécurité*. Si vous utilisez une URL Base, ajoutez-la (`http://192.168.1.10:7878/radarr`).

| Application | Port par défaut | Sur TrueNAS |
|---|---|---|
| Radarr | 7878 | 30025 |
| Sonarr | 8989 | 30027 |
| Lidarr | 8686 | |
| Whisparr | 6969 | |
| Prowlarr | 9696 | |

## Utilisation

Chaque tâche est un parcours en étapes (l'indicateur est en haut), et **toutes les actions sont dans la barre du bas** : on ne fait qu'avancer.

**Exporter une configuration**, pour la réutiliser vous-même ou l'envoyer à quelqu'un :

1. Ouvrez **Export** et choisissez l'instance. Sa configuration se charge toute seule.
2. Décochez ce que vous ne voulez pas. Cocher un profil coche aussi ce dont il dépend.
3. **Téléchargez le fichier.** Gardez-le comme sauvegarde, réimportez-le sur une autre de vos instances, ou envoyez-le.

**Importer une configuration** :

1. **Choisissez** l'instance à configurer, puis d'où vient la configuration : *un fichier ou du JSON collé* (un export Portarr, un format ou un profil TRaSH), *une autre instance* de la même application, ou les *TRaSH Guides* (Radarr et Sonarr). Cliquez sur **Vérifier les changements**.
2. **Vérifiez** la liste de ce qui sera créé, modifié ou ignoré. Décochez ce que vous ne voulez pas, puis **Appliquez**. *Modifier* (ou l'étape 1 de l'indicateur) ramène en arrière sans rien perdre.
3. **Terminé** : le résumé et le lien vers la sauvegarde de la cible.

**Revenir en arrière** : ouvrez **Sauvegardes**, puis réimportez le fichier voulu (*Import → Un fichier*) avec *écraser* coché. Les éléments créés entre-temps ne sont pas supprimés.

*Écraser les éléments existants* concerne les éléments appariés par nom : formats personnalisés, profils de qualité, profils de synchronisation, indexeurs et proxys. Les tailles par qualité, le nommage et la gestion des médias sont toujours mis à jour s'ils sont cochés.

### Profils TRaSH Guides

Un profil TRaSH ne contient que des *références* : ses formats obligatoires sont nommés, et leurs scores se trouvent dans le fichier de chaque format, selon le *jeu de scores* du profil. Portarr résout tout cela :

1. Il télécharge une fois le [dépôt des guides](https://github.com/TRaSH-Guides/Guides) (environ 25 Mo, dont il ne garde que 1,2 Mo de JSON) et le garde 12 heures dans `/config/cache`.
2. Pour le profil choisi, il rassemble les formats obligatoires et les groupes optionnels qui s'y appliquent, avec chaque score. Ce que recommandent les guides est coché d'office.
3. Il construit un export Portarr complet (profil, scores, définitions des formats) qui passe par l'aperçu et la sauvegarde habituels.

Les qualités gardent l'ordre des guides, et toute qualité que le guide ne mentionne pas est ajoutée en bas, désactivée.

- **Un accès Internet est nécessaire** la première fois et pour *Mettre à jour les guides*. Hors ligne, la copie en cache est utilisée même périmée. Coller des formats personnalisés fonctionne hors ligne.
- **Radarr et Sonarr uniquement** : les guides ne couvrent rien d'autre.
- Les tailles par qualité et le nommage des guides ne sont pas encore importés, et leur fichier de *conflits* n'est pas appliqué. Lisez la description de chaque groupe (par exemple, ne scorez qu'un seul des deux formats x265).
- `TRASH_GUIDES_URL` désigne une autre archive, par exemple un miroir.

### Secrets des indexeurs Prowlarr

Prowlarr masque les clés API, mots de passe et noms d'utilisateur dans son API : ils **ne peuvent pas être exportés**. Portarr ne les écrit jamais dans un fichier. À l'import :

- un **nouvel** indexeur qui en a besoin est créé **désactivé**, sans test de connexion, qui échouerait. Renseignez ses secrets sur la cible, puis activez-le ;
- un indexeur **existant** conserve ses secrets, et son état activé n'est pas modifié s'il en a ;
- les indexeurs publics n'ont pas de secrets et sont créés normalement.

Les *Applications* (les liens Prowlarr → Radarr/Sonarr, qui contiennent des clés API) et les clients de téléchargement ne sont volontairement pas gérés : ils dépendent de votre environnement.

## Mise à jour

| Installation | Commande ou action |
|---|---|
| Docker Compose | `git pull && docker compose up -d --build` |
| docker run | `docker pull ghcr.io/ali0cha/portarr:latest`, puis supprimez et recréez le conteneur (le volume est conservé) |
| TrueNAS | *Apps → portarr → Edit → Save*. Avec `pull_policy: always` dans le YAML, TrueNAS retélécharge l'image |

Si TrueNAS garde l'ancienne image, lancez `sudo docker pull ghcr.io/ali0cha/portarr:latest` depuis le shell du NAS, puis refaites *Edit → Save*.

L'image publiée ne change que lorsque la dernière construction de l'onglet **Actions** de ce dépôt est verte. Pour savoir ce qui tourne, lisez le bas de la barre latérale : la **version** et le **commit** dont l'image a été construite (par exemple `build a1b2c3d`). Une image construite à la main affiche `build dev`.

Vos instances et vos sauvegardes sont dans `/config` et survivent aux mises à jour.

## Référence

### Sécurité

Portarr détient les clés API de vos instances. Gardez-le sur votre réseau local et définissez `AUTH_USER` et `AUTH_PASSWORD` (authentification HTTP basique) sauf si le port est réservé à un réseau de confiance. Ne l'exposez pas directement sur Internet ; placez-le derrière un reverse proxy HTTPS si nécessaire. `/healthz` reste public.

### Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `PORT` | `8765` | Port d'écoute dans le conteneur |
| `CONFIG_DIR` | `/config` | `instances.json` (mode 600), `backups/` et `cache/` |
| `TRASH_GUIDES_URL` | archive GitHub du dépôt TRaSH | Adresse de l'archive `.tar.gz` des guides |
| `AUTH_USER`, `AUTH_PASSWORD` | vides | Activent l'authentification si les deux sont définies |

### Format du fichier d'export

JSON lisible et versionné (`"format": "portarr"`, `"version": 1`). Les profils référencent les formats et les qualités par nom :

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

### Design

L'interface reprend la structure de la dernière version de Sonarr : en-tête coloré, barre latérale, cartes, police Inter et palette OKLCH claire / sombre. Chaque application de la suite [Servarr](https://wiki.servarr.com/) a sa teinte (Sonarr cyan, Radarr jaune, Lidarr vert, Readarr rouge sombre, Prowlarr orange, Whisparr rose), et **Portarr prend la teinte libre, le violet**. Les badges d'instance gardent la couleur de leur application. Le logo est [`app/static/logo.svg`](app/static/logo.svg). La police Inter (SIL OFL, voir `app/static/fonts/LICENSE-Inter.txt`) est embarquée : rien n'est chargé depuis Internet.

## Développement

Le backend est du FastAPI (`app/`) et le frontend du JavaScript simple, sans étape de build (`app/static/`).

```bash
./run_tests.sh                                   # tests dans un conteneur Python jetable
python -m tests.fake_arr radarr-a:7001 radarr-b:7002 sonarr-a:7003 sonarr-b:7004 lidarr-a:7005 lidarr-b:7006 whisparr-a:7007 whisparr-b:7008 prowlarr-a:7009 prowlarr-b:7010
                                                 # faux serveurs, clé « demo-key » : un « -a » rempli et un « -b » cible par application
python -m tests.fake_trash 7100                  # mini dépôt TRaSH hors ligne (TRASH_GUIDES_URL=http://127.0.0.1:7100/Guides.tar.gz)
CONFIG_DIR=./config python -m app                # l'application sur http://localhost:8765
```

- `tests/fake_arr.py` simule les API en mémoire (noms uniques, cutoffs valides, IDs de formats, secrets masqués, `forceSave`). Les tests couvrent l'aller-retour entre deux instances aux IDs différents, l'idempotence d'un second import et l'absence de secrets dans les exports.
- Les textes de l'interface sont dans la table `I18N` de `app/static/app.js`. `tests/test_i18n.py` garde l'anglais et le français alignés, et `tests/test_readmes.py` fait de même pour les deux README.
- Pour publier une nouvelle version, changez `__version__` dans `app/__init__.py`. La construction GitHub ajoute le commit.

## Pistes d'évolution

Tailles par qualité et nommage TRaSH, prise en compte du fichier de conflits TRaSH, profils de délai, release profiles (Sonarr, Lidarr), Readarr, synchronisation avec suppression, traduction des messages renvoyés par les serveurs.
