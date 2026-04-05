"""
One-time / idempotent bootstrap: ensure at least one admin exists so the API is usable immediately.
"""
from __future__ import annotations

import logging
import os

from sqlalchemy.orm import Session

from app.core.auth import hash_password
from app.db.database import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_EMAIL = "admin@gmail.com"
DEFAULT_ADMIN_PASSWORD = "admin123456"


def ensure_bootstrap_admin() -> None:
    """
    If no user has role ``admin``, create or upgrade the bootstrap account.

    Idempotent: when at least one admin already exists, does nothing.
    Does not log passwords or secrets.
    """
    admin_email = os.getenv("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL).strip()
    admin_password = os.getenv("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    db: Session = SessionLocal()
    try:
        if db.query(User).filter(User.role == "admin").first() is not None:
            logger.info("Admin already exists, skipping bootstrap")
            return

        existing = db.query(User).filter(User.email == admin_email).first()
        if existing is not None:
            existing.name = existing.name or "Admin"
            existing.role = "admin"
            existing.is_active = True
            existing.password = hash_password(admin_password)
            db.commit()
            logger.info("Bootstrap admin: existing user promoted to admin")
            return

        user = User(
            name="Admin",
            email=admin_email,
            role="admin",
            is_active=True,
            password=hash_password(admin_password),
        )
        db.add(user)
        db.commit()
        logger.info("Bootstrap admin created")
    except Exception:
        db.rollback()
        logger.exception("Bootstrap admin failed")
        raise
    finally:
        db.close()
