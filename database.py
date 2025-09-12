import logging
from typing import Optional
import functools

import psycopg2
from psycopg2.pool import SimpleConnectionPool

from data import db_dbname, db_host, db_user, db_password
from schemas import User

logger = logging.getLogger('httpx')


def with_db_connection(autocommit=True):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            conn = None
            try:
                conn = self._get_conn()
                conn.autocommit = autocommit
                result = func(self, conn, *args, **kwargs)
                return result
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                logger.error(f'Database error in {func.__name__}: {e}')
                return None
            finally:
                if conn:
                    self._put_conn(conn)
        return wrapper
    return decorator


class Database:
    _instance = None
    _pool = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __del__(self):
        Database._instance = None

    def __init__(self):
        if Database._pool is None:
            try:
                Database._pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dbname=db_dbname,
                    host=db_host,
                    user=db_user,
                    password=db_password
                )
                with Database._pool.getconn() as conn:
                    conn.autocommit = True
                    with conn.cursor() as cur:
                        files = [
                            'sql/users.sql',
                        ]
                        for file in files:
                            with open(file, 'r', encoding='utf-8') as f:
                                cur.execute(f.read())

            except psycopg2.OperationalError as e:
                logger.error(f'Error creating db connection pool: {e}')

    @staticmethod
    def _get_conn():
        return Database._pool.getconn()

    @staticmethod
    def _put_conn(conn):
        Database._pool.putconn(conn)

    @with_db_connection()
    def get_user(self, conn, tg_id: int) -> Optional[User]:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM get_user(%s);', (tg_id,))
            user = cur.fetchone()
            if user:
                return User(
                    id=user[0],
                    tg_id=user[1],
                    tg_username=user[2],
                    tg_first_name=user[3],
                    tg_last_name=user[4],
                    lichess_username=user[5]
                )
            return None

    @with_db_connection()
    def get_all_users(self, conn) -> list[User]:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM get_all_users();')
            users = cur.fetchall()
            return [
                User(
                    id=user[0],
                    tg_id=user[1],
                    tg_username=user[2],
                    tg_first_name=user[3],
                    tg_last_name=user[4],
                    lichess_username=user[5]
                ) for user in users
            ]

    @with_db_connection()
    def add_user(self, conn, tg_id: int, tg_username: str, tg_first_name: str, tg_last_name: str) -> Optional[str]:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    'SELECT add_user(%s, %s, %s, %s);',
                    (tg_id, tg_username, tg_first_name, tg_last_name)
                )
            except Exception as e:
                return str(e)

    @with_db_connection()
    def update_lichess_username(self, conn, tg_id: int, new_lichess_username: str) -> None:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT update_lichess_username(%s, %s);',
                (tg_id, new_lichess_username)
            )