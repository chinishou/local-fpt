"""
Database setup for LocalFPT - Synchronous SQLite.
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool


_engine = None
_session_factory = None
_db_path = None


def get_db_path():
    return _db_path


def init_db(db_path=None):
    global _engine, _session_factory, _db_path

    if db_path is None:
        db_path = os.environ.get('FPT_DB_PATH', 'fpt_local.db')

    _db_path = os.path.abspath(db_path)

    _engine = create_engine(
        f'sqlite:///{_db_path}',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
        echo=False,
    )

    @event.listens_for(_engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    from local_fpt.db.models import Base
    Base.metadata.create_all(_engine)

    _session_factory = sessionmaker(bind=_engine)


def get_session():
    return scoped_session(_session_factory)()


def reset_session():
    scoped_session(_session_factory).remove()
