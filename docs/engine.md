# Zanalyze ↔ Zanalyze Engine

La PWA **Zanalyze** (ce repo, GitHub `Zanalyze`) affiche matchs et tips.  
Le calcul et l’ingest **ESPN** vivent dans un git **séparé** :

→ **[Zanalyze-Engine](https://github.com/Stevy64/Zanalyze-Engine)**  
  (copie locale : `../Zanalyze-Engine`)

Sur **PythonAnywhere**, le worker Django n’appelle pas ESPN en direct : le moteur tourne sur GitHub Actions (ou Oracle Always Free) et publie `exports/matchs.json`.

**Activer Actions** (écran « Choose a workflow ») :  
[docs/actions.md dans l’engine](https://github.com/Stevy64/Zanalyze-Engine/blob/main/docs/actions.md)

```bash
# Sur PA, toutes les ~2 h (Scheduled task) :
python manage.py importer_snapshot --url https://raw.githubusercontent.com/Stevy64/Zanalyze-Engine/main/exports/matchs.json
```

Variables :

| Variable | Rôle |
|----------|------|
| `ZANALYZ_SYNC_LIVE=0` | Worker Django importe le snapshot (pas d’ingest live) |
| `ZANALYZ_SNAPSHOT_URL` | URL du JSON engine |
| `ZANALYZ_MOTEUR_URL` | Optionnel (VPS Docker). Sur PA, laisser vide |

Note : le champ JSON / DB `sofascore_id` est le **contrat snapshot v1** (ids ESPN). Ne pas le renommer côté PWA.

Doc Oracle moteur : [oracle.md](https://github.com/Stevy64/Zanalyze-Engine/blob/main/docs/oracle.md).
