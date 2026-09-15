# Architecture Zanalyze + Zanalyze Engine

Deux git :

- **Zanalyze** (ce repo `Zanalyze`) : PWA Django, admin, VIP
- **[Zanalyze Engine](https://github.com/Stevy64/Zanalyze-Engine)** : ESPN, modèles v3.1, snapshot v1

Sur **PythonAnywhere**, Django importe le JSON produit par l’engine (`ZANALYZ_SYNC_LIVE=0`). Voir [engine.md](engine.md).

Sur **VPS Docker**, l’app peut rester autonome (`ZANALYZ_SYNC_LIVE=1`) ou importer le même snapshot.

## Schéma (VPS Docker)

```text
                    ┌─────────────┐
   Internet ───────►│   nginx     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ zanalyz-web │  PWA + API + Admin
                    └──────┬──────┘
                           │ HTTP analyse (optionnel)
                    ┌──────▼──────┐
                    │ moteur      │  FastAPI v3.1 (image locale)
                    └─────────────┘

        ┌──────────────────────────────────────┐
        │ worker (~2 h)                        │
        │  SYNC_LIVE=1 : ingest + calculer     │
        │  SYNC_LIVE=0 : importer_snapshot     │
        │  puis regler_options + purger_chat   │
        └──────────────────────────────────────┘
```

## Schéma (PythonAnywhere + Engine)

```text
ESPN → Zanalyze-Engine (Actions / Oracle)
              ↓ exports/matchs.json (GitHub)
Zanalyze PA  ← importer_snapshot --url
```

## Granularité (volontairement limitée)

| Service | Image | Rôle |
|--------|-------|------|
| **nginx** | nginx | TLS/HTTP, static / media |
| **web** | `zanalyz-prod` | UI + API + admin |
| **moteur** | `zanalyz-moteur` | Calculs probabilités / tips |
| **worker** | `zanalyz-prod` | Pipeline autonome |
| **db** | postgres | Données |
| **redis** | redis | Lock jobs + présence Salon VIP |

Pas de découpage plus fin (auth service, etc.) : surcoût sans gain pour cette app.

## Variables clés

```bash
ZANALYZ_MOTEUR_URL=http://moteur:8001
ZANALYZ_REDIS_URL=redis://redis:6379/0
ZANALYZ_WORKER_INTERVAL=7200          # secondes entre deux pipelines
ZANALYZ_SYNC_LIVE=1                   # 0 = snapshot Engine (PythonAnywhere)
ZANALYZ_SNAPSHOT_URL=                 # raw GitHub du JSON engine
ZANALYZ_SYNC_PAGES=1
ZANALYZ_SYNC_CONTEXTE=0               # 1 = H2H/forme (plus lent)
```

Si `ZANALYZ_MOTEUR_URL` est vide, Django calcule **en local** (fallback).

## Lancer

```bash
# Prod
cp .env.example .env   # secrets
make prod-build        # web + moteur + worker + db + redis + nginx

# Dev (web + moteur ; worker optionnel)
make dev-d
make dev-worker        # profile Compose
```

## API moteur

- `GET  /health`
- `POST /v1/analyser` — lot de matchs + classement journée
- `POST /v1/analyser-un` — un match
- Docs OpenAPI : `http://moteur:8001/docs` (réseau Docker)

## Fiches clubs / logos

Chaîne côté serveur (noms de fournisseurs **non exposés** à l’UI) :

1. API calendrier principale  
2. Secours TheSportsDB (logos, forme, classement)  
3. Historique local en base  

Proxy logos : `GET /api/v1/equipes/<id>/logo/`

## PythonAnywhere

Pas de Docker : pas de worker container. Utilise les **Tasks** PA ou un cron
externe qui appelle les mêmes `manage.py` (voir [pythonanywhere.md](pythonanywhere.md)).
