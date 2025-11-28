Oazis est un bot Telegram minimal pour suivre l'hydratation quotidienne et envoyer des rappels programmés.

## Démarrage rapide
- Copier `.env.example` vers `.env` et renseigner `TELEGRAM_BOT_TOKEN` (et éventuellement `DATABASE_URL`, `TIMEZONE`).
- Installer les dépendances : `uv sync`.
- Lancer le bot : `uv run python main.py`.

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
