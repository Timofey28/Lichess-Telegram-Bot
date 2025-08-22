from typing import Optional
import psycopg2

from data import db_dbname, db_host, db_user, db_password
from schemas import User


class Database:
    __instance = None

    __db_name = db_dbname
    __db_host = db_host
    __db_user = db_user
    __db_password = db_password

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __del__(self):
        Database.__instance = None

    def __init__(self):
        if not hasattr(self, 'conn'):
            self.conn = psycopg2.connect(
                dbname=Database.__db_name,
                host=Database.__db_host,
                user=Database.__db_user,
                password=Database.__db_password,
            )
            self.conn.autocommit = True
            self.cur = self.conn.cursor()

            files = [
                'sql/users.sql',
            ]

            for file in files:
                with open(file, 'r', encoding='utf-8') as f:
                    self.cur.execute(f.read())

    def get_user(self, tg_id: int) -> Optional[User]:
        self.cur.execute('SELECT * FROM get_user(%s);', (tg_id,))
        user = self.cur.fetchone()
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

    def add_user(self, tg_id: int, tg_username: str, tg_first_name: str, tg_last_name: str) -> Optional[str]:
        try:
            self.cur.execute(
                'SELECT add_user(%s, %s, %s, %s);',
                (tg_id, tg_username, tg_first_name, tg_last_name)
            )
        except Exception as e:
            return str(e)

    def update_lichess_username(self, tg_id: int, new_lichess_username: str) -> None:
        self.cur.execute(
            'SELECT update_lichess_username(%s, %s);',
            (tg_id, new_lichess_username)
        )