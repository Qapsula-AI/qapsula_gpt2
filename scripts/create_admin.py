#!/usr/bin/env python3
"""
Скрипт для создания администратора системы.

Использование:
    # Из Docker контейнера
    docker-compose -f docker-compose.dev.yml exec app python scripts/create_admin.py

    # Локально
    python scripts/create_admin.py

Требования:
    - В .env должен быть установлен ADMIN_PASSWORD
    - База данных должна быть инициализирована (миграции выполнены)
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import User
from app.auth.password import hash_password

# Загружаем переменные окружения
load_dotenv()


def create_admin_user() -> None:
    """Создать admin пользователя."""
    db: Session = SessionLocal()

    try:
        # Проверяем существование admin пользователя
        existing_admin = db.query(User).filter(User.username == "admin").first()

        if existing_admin:
            print("❌ Admin пользователь уже существует")
            print(f"   ID: {existing_admin.id}")
            print(f"   Username: {existing_admin.username}")
            print(f"   Email: {existing_admin.email}")
            print(f"   Создан: {existing_admin.created_at}")
            return

        # Получаем пароль из переменных окружения
        admin_password = os.getenv("ADMIN_PASSWORD")

        if not admin_password:
            print("❌ Ошибка: ADMIN_PASSWORD не установлен в переменных окружения")
            print("   Добавьте ADMIN_PASSWORD в файл .env или .env.local")
            sys.exit(1)

        # Создаём пользователя
        admin = User(
            username="admin",
            email="admin@qapsula.local",
            hashed_password=hash_password(admin_password),
            full_name="Administrator",
            is_active=True,
            is_superuser=True
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("✅ Admin пользователь создан успешно!")
        print(f"   ID: {admin.id}")
        print(f"   Username: admin")
        print(f"   Email: admin@qapsula.local")
        print(f"   Является суперпользователем: Да")
        print()
        print("🔐 Используйте эти учетные данные для входа:")
        print(f"   Username: admin")
        print(f"   Password: {admin_password}")
        print()
        print("⚠️  ВАЖНО: Сохраните эти данные в надежном месте!")

    except Exception as e:
        print(f"❌ Ошибка при создании admin пользователя: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Создание администратора системы")
    print("=" * 60)
    print()

    create_admin_user()