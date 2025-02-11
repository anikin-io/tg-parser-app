import os
from pathlib import Path

from ...core.entities.account import Account, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from config.statuses import (
    STATUS_FREE,
    STATUS_IN_WORK,
    STATUS_LIMIT_REACHED,
    STATUS_ON_PAUSE,
    STATUS_SPAM_BLOCK,
)

VALID_STATUSES = {STATUS_IN_WORK, STATUS_LIMIT_REACHED, STATUS_SPAM_BLOCK, STATUS_FREE, STATUS_ON_PAUSE}

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_PATH = BASE_DIR / "sqlite_database" / "telegram_accounts.db"
os.makedirs(DATABASE_PATH.parent, exist_ok=True)

engine = create_engine(f"sqlite:///{DATABASE_PATH}", echo=False)
Session = sessionmaker(bind=engine)


def init_db():
    """Создание таблиц, если их нет."""
    Base.metadata.create_all(engine)


def add_account(
    phone, name, proxy_ip, proxy_port, proxy_username, proxy_password, status=STATUS_FREE
):
    """Добавляет новый аккаунт в БД."""
    session = Session()
    new_account = Account(
        phone=phone,
        name=name,
        proxy_ip=proxy_ip,
        proxy_port=proxy_port,
        proxy_username=proxy_username,
        proxy_password=proxy_password,
        status=status,
    )
    session.add(new_account)
    session.commit()
    session.close()


def get_all_accounts():
    """Получает список всех аккаунтов."""
    session = Session()
    accounts = session.query(Account).all()
    session.close()
    return accounts


def get_free_accounts():
    """Получает все аккаунты со статусом 'свободен'."""
    session = Session()
    free_accounts = session.query(Account).filter(Account.status == STATUS_FREE).all()
    session.close()
    return free_accounts


def get_account_by_phone(phone):
    """Ищет аккаунт по номеру телефона."""
    session = Session()
    account = session.query(Account).filter(Account.phone == phone).first()
    session.close()
    return account


def update_status_by_phone(phone, new_status):
    """Обновляет статус аккаунта по номеру телефона."""
    
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Некорректный статус: {new_status}. Допустимые значения: {VALID_STATUSES}")
    
    session = Session()
    try:
        account = session.query(Account).filter(Account.phone == phone).one() 
        account.status = new_status
        session.commit()
    except NoResultFound:
        print(f"Аккаунт с телефоном {phone} не найден.")
    except IntegrityError:
        session.rollback()
        print(f"Ошибка в процессе обновления данных аккаунта {phone}.")
    finally:
        session.close()


def reset_status_to_free():
    """Изменяет статус всех аккаунтов с 'в работе' на 'свободен'."""
    session = Session()
    accounts_in_work = session.query(Account).filter(Account.status == STATUS_IN_WORK).all()

    for account in accounts_in_work:
        account.status = STATUS_FREE

    session.commit()
    session.close()
