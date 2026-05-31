# DevOps Monitoring Dashboard

> Système de monitoring temps réel construit en Python, containerisé avec Docker, et déployé sur Azure via un pipeline CI/CD GitHub Actions.

## Architecture

```
GitHub Actions CI/CD
  ├── lint (flake8)
  ├── test (pytest --cov ≥ 75 %)
  ├── build & push → Azure Container Registry
  └── deploy → Azure Container Apps
         │
         ▼
  devops-monitor-api  (FastAPI — port 8000)
  devops-monitor-dashboard  (Streamlit — port 8501)
```

## Prérequis

- Python 3.11+
- Docker & Docker Compose
- Make
- (Pour le déploiement) Azure CLI + compte Azure

## Lancement local

```bash
# 1. Cloner le dépôt
git clone <url-du-repo>
cd devops-monitor

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et renseigner API_KEY avec une valeur forte

# 3. Démarrer la stack
make up

# 4. Vérifier que tout tourne
make logs
```

- **API** : http://localhost:8000/docs
- **Dashboard** : http://localhost:8501

## Commandes disponibles

| Commande      | Description                              |
|---------------|------------------------------------------|
| `make up`     | Build & démarre la stack Docker          |
| `make down`   | Arrête la stack et supprime les volumes  |
| `make logs`   | Affiche les logs en temps réel           |
| `make test`   | Lance pytest avec coverage ≥ 75 %        |
| `make lint`   | Lint flake8 sur tout le code             |
| `make dev-api`| Lance l'API en local (uvicorn --reload)  |

## Variables d'environnement

| Variable        | Description                                   | Exemple               |
|-----------------|-----------------------------------------------|-----------------------|
| `API_KEY`       | Clé d'accès à l'API (header `X-API-Key`)      | `my-super-secret-key` |
| `API_BASE_URL`  | URL de l'API vue par le dashboard             | `http://api:8000`     |

> ⚠️ Ne jamais commiter `.env`. Seul `.env.example` est versionné.

## Endpoints API

| Méthode  | Chemin                     | Auth      | Description                     |
|----------|----------------------------|-----------|---------------------------------|
| `GET`    | `/health`                  | —         | Liveness probe                  |
| `GET`    | `/metrics`                 | —         | Métriques CPU/mémoire/disque    |
| `WS`     | `/ws/metrics`              | —         | Stream JSON toutes les secondes |
| `POST`   | `/servers`                 | API Key   | Enregistrer un serveur          |
| `GET`    | `/servers`                 | —         | Lister les serveurs + statut    |
| `DELETE` | `/servers/{id}`            | API Key   | Supprimer un serveur            |
| `POST`   | `/servers/{id}/check`      | API Key   | Health check manuel             |

## URLs live (Azure)

> À remplir après le déploiement

- **API** : `https://<api-url>.azurecontainerapps.io/docs`
- **Dashboard** : `https://<dashboard-url>.azurecontainerapps.io`

## Tests

```bash
make test
# ou directement :
pytest tests/ -v --cov=api --cov-fail-under=75 --cov-report=term-missing
```

## Stack technique

| Couche | Technologie |
|--------|------------|
| Langage | Python 3.11 |
| API | FastAPI + Uvicorn |
| Frontend | Streamlit |
| Métriques | psutil |
| Auth | API Key (`X-API-Key`) |
| Containers | Docker, Docker Compose |
| Tests | pytest + pytest-cov |
| CI/CD | GitHub Actions |
| Registry | Azure Container Registry |
| Hosting | Azure Container Apps |
