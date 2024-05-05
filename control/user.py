"""User

Handles the user login credentials"""

from hashlib import md5
from sqlite3 import Connection, Cursor, connect
from typing import Optional


class User:
    """Stores the username, password, and name in memory"""
    __name = Optional[str]
    __username = Optional[str]
    __password = Optional[str]

    @classmethod
    def get_connection(cls) -> tuple[Connection, Cursor]:
        """Returns the connection and cursor from the DB"""
        connection = connect("data.db")
        cursor = connection.cursor()
        return connection, cursor

    @classmethod
    def has_permission(cls) -> bool:
        """Returns True if the user has permission to access Tasks"""
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
        """Logs the current username"""
        cls.__username = username

    @classmethod
    def set_password(cls, password: str) -> None:
        """Logs the current password"""
        hash_function = md5(password)
        cls.__password = hash_function.hexdigest()

    @classmethod
    def set_hashed_password(cls, hashed_password: str) -> None:
        """Sets the password hash"""
        cls.__password = hashed_password

    @classmethod
    def get_username(cls) -> str:
        """Returns the current logged in user"""
        return cls.__username

    @classmethod
    def get_hashed_password(cls) -> str:
        """Returns the password hash"""
        return cls.__password

    @classmethod
    def get_name(cls) -> str:
        """Returns the name of the logged in user"""
        return cls.__name
