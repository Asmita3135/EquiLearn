"""
Database configuration.
Set DATABASE_URL in the environment to point at PostgreSQL in production.

  PostgreSQL:  postgresql://user:password@host:5432/equilearn
  SQLite:      sqlite:///./equilearn.db   (default – no server needed)
"""
import os

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./equilearn.db")
