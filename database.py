import logging
from typing import Optional
import psycopg2
from psycopg2.pool import SimpleConnectionPool

from data import db_dbname, db_host, db_user, db_password
from schemas import User

logger = logging.getLogger('httpx')


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

    def get_user(self, tg_id: int) -> Optional[User]:
        conn = None
        try:
            conn = self._get_conn()
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
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.error(f'Database error in get_user: {e}')
            return None
        finally:
            if conn:
                self._put_conn(conn)

    def get_all_users(self) -> list[User]:
        conn = None
        try:
            conn = self._get_conn()
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
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.error(f'Database error in get_user: {e}')
            return []
        finally:
            if conn:
                self._put_conn(conn)

    def add_user(self, tg_id: int, tg_username: str, tg_first_name: str, tg_last_name: str) -> Optional[str]:
        conn = None
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT add_user(%s, %s, %s, %s);',
                    (tg_id, tg_username, tg_first_name, tg_last_name)
                )
        except Exception as e:
            return str(e)
        finally:
            if conn:
                self._put_conn(conn)

    def update_lichess_username(self, tg_id: int, new_lichess_username: str) -> None:
        conn = None
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT update_lichess_username(%s, %s);',
                    (tg_id, new_lichess_username)
                )
        finally:
            if conn:
                self._put_conn(conn)