Oazis est un bot Telegram minimal pour suivre l'hydratation quotidienne et envoyer des rappels programmés.

## Démarrage rapide
- Copier `.env.example` vers `.env` et renseigner `TELEGRAM_BOT_TOKEN` (et éventuellement `DATABASE_URL`, `TIMEZONE`).
- Installer les dépendances : `uv sync`.
- Lancer le bot : `uv run python main.py`.

## Déploiement Docker (ex. sur un VPS)

### 1. Préparer la configuration
- Copier `.env.example` vers `.env` et renseigner au minimum `TELEGRAM_BOT_TOKEN`.
- Sur le VPS, le fichier `.env` sera monté dans le conteneur.

### 2. Construire l'image
- Sur le VPS (ou en local puis `docker push`), depuis la racine du projet :
  - `docker build -t oazis-bot .`

### 3. Créer un dossier pour la base SQLite
- Sur le VPS, par exemple :
  - `mkdir -p /srv/oazis-data`

### 4. Lancer le conteneur
- Exemple de commande :
  - `docker run -d --name oazis \\`
  - `  --restart unless-stopped \\`
  - `  --env-file .env \\`
  - `  -v /srv/oazis-data:/app/data \\`
  - `  oazis-bot`

Notes :
- Le bot utilise le long polling Telegram : aucun port n'a besoin d'être exposé.
- Le volume `/srv/oazis-data:/app/data` permet de conserver la base SQLite (`./data/oazis.db`) entre les redémarrages.

## Structure du projet
- `oazis/config`: chargement de la configuration via Pydantic.
- `oazis/logger.py`: configuration centralisée de Loguru.
- `oazis/db`: modèles SQLModel et utilitaires de session SQLite.
- `oazis/services`: logique métier (hydration).
- `oazis/bot`: bot aiogram et handlers.
- `oazis/scheduler`: planification APScheduler pour les rappels.
- `tests`: espace pour les tests automatisés.

## Notes
- La base SQLite peut être montée en volume dans Docker (chemin par défaut `./data/oazis.db`).
- Tous les secrets doivent passer par les variables d'environnement, jamais en dur.
