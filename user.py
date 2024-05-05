from hashlib import md5
from sqlite3 import Connection, Cursor, connect
from typing import Optional


class User:
    __username = Optional[str]
    __password = Optional[str]
    __name = Optional[str]
    __cursor = Optional[Cursor]

    @classmethod
    def get_connection(cls) -> tuple[Connection, Cursor]:
        connection = connect("data.db")
        cursor = connection.cursor()
        return connection, cursor

    @classmethod
    def has_permission(cls) -> bool:
        _, cursor = cls.get_connection()
        cursor.execute(
            "SELECT * FROM USERS WHERE USERNAME = ? AND PASSWORD = ?",
            (cls.__username, cls.__password),
        )
        result = cursor.fetchall()
        if len(result) > 0:
            cls.__name = result[0][3]
            return True
        return False

    @classmethod
    def set_username(cls, username: str) -> None:
        cls.__username = username

    @classmethod
    def set_password(cls, password: str) -> None:
        hashFunction = md5(password)
        cls.__password = hashFunction.hexdigest()

    @classmethod
    def set_hashed_password(cls, hashedPassword) -> None:
        cls.__password = hashedPassword

    @classmethod
    def get_username(cls) -> str:
        return cls.__username

    @classmethod
    def get_hashed_password(cls) -> str:
        return cls.__password

    @classmethod
    def get_name(cls) -> str:
        return cls.__name
