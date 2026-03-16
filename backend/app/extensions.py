"""
Shared Flask extensions used across the app.

- db: talk to the database (SQLAlchemy)
- migrate: run database migrations (Flask-Migrate / Alembic)
- jwt: create and verify JWT tokens (Flask-JWT-Extended)
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

