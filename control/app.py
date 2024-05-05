"""App

Handles the I/O and database queries
"""

from hashlib import md5
from sqlite3 import connect, Connection, Cursor
from time import strftime
from typing import Optional

from flask import Flask, render_template, request, make_response, redirect, Response

from control.user import User

app = Flask(__name__)


TASK_ID_IS_NONE_ERROR =(
    "Error: No task associated with that ID. Maybe someone else already deleted it?"
)


def get_connection() -> tuple[Connection, Cursor]:
    """Returns the SQLite"""
    connection = connect("data.db")
    cursor = connection.cursor()
    return connection, cursor


def is_installed() -> bool:
    """Returns True if a user already exists"""
    _, cursor = get_connection()
    cursor.execute("SELECT COUNT( 1 ) FROM USERS")
    has_user = cursor.fetchone()[0]
    return has_user > 0


def add_request(request_type: str) -> None:
    """Adds a task to the DB"""
    connection, cursor = get_connection()
    creation_date = strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute(
        "INSERT INTO UPDATE_REQUESTS( UPDATE_TYPE, DONE, CREATION_DATE ) VALUES"
        " ( ?, 'N', ? )",
        (request_type, creation_date),
    )
    connection.commit()


@app.before_request
def before_request() -> Optional[str]:
    """Determines which page to show the user based on install and login status"""
    if request.path == "/install":
        return None
    if not is_installed():
        return render_template("install_prettypi.html")
    if request.path == "/login":
        return None
    if request.cookies.get("prettypi_username") is not None:
        User.set_username(request.cookies.get("prettypi_username"))
        User.set_hashed_password(request.cookies.get("prettypi_password"))
        return None if User.has_permission() else render_template("login.html")
    return render_template("login.html")


@app.route("/")
def main() -> str:
    """This is the landing page"""
    return render_template("main_page.html", name=User.get_name())


@app.route("/install", methods=["POST"])
def install() -> str:
    """Initializes the PrettyPi site for the network"""
    connection, cursor = get_connection()
    if is_installed():
        return render_template(
            "installer_message.html",
            message="PrettyPi Already Installed",
            type="danger",
        )
    if (
        not request.form["username"]
        or not request.form["password"]
        or not request.form["name"]
    ):
        return render_template(
            "installer_message.html", message="Please fill all fields", type="danger"
        )
    hash_function = md5(request.form["password"].encode("utf-8"))
    hashed_password = hash_function.hexdigest()
    cursor.execute(
        "INSERT INTO USERS( USER_ID, USERNAME, PASSWORD, NAME ) VALUES ( NULL, ?, ?, ? )",
        [request.form["username"], hashed_password, request.form["name"]],
    )
    connection.commit()
    return render_template(
        "installer_message.html",
        message="Congratulations! PrettyPi has been initialized. "
        "Go back to homepage to start using it",
        type="success",
    )


@app.route("/login", methods=["POST"])
def login() -> Response | str:
    """Determines if the login information is valid"""
    User.set_username(request.form["username"])
    User.set_password(request.form["password"].encode("utf-8"))
    if User.has_permission():
        response = make_response(redirect("/"))
        response.set_cookie("prettypi_username", User.get_username())
        response.set_cookie("prettypi_password", User.get_hashed_password())
        return response
    return f'Invalid username ("{User.get_username()}") or password'


@app.route("/logout")
def logout() -> Response:
    """Logs the current user out"""
    response = make_response(redirect("/"))
    response.set_cookie("prettypi_username", "")
    response.set_cookie("prettypi_password", "")
    return response


@app.route("/tasks")
def tasks_main():
    """Retrieves the completed, running, and done tasks from the DB to display"""
    _, cursor = get_connection()
    cursor.execute("SELECT * FROM TODO WHERE DONE = 'N' ORDER BY CREATION_DATE DESC")
    tasks = cursor.fetchall()
    cursor.execute("SELECT * FROM TODO WHERE DONE = 'Y' ORDER BY CREATION_DATE DESC")
    done_tasks = cursor.fetchall()
    cursor.execute("SELECT * FROM TODO WHERE WORKING_ON = 'Y'")
    working_task = cursor.fetchone()
    return render_template(
        "tasks.html",
        tasks=tasks,
        done_tasks=done_tasks,
        name=User.get_name(),
        working_task=working_task,
    )


@app.route("/add_task", methods=["POST"])
def new_task():
    """Adds a new task to the DB"""
    connection, cursor = get_connection()
    if not request.form["task_details"]:
        return render_template(
            "message.html", message="The details should not be empty", type="warning"
        )
    creation_date = strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute(
        "INSERT INTO TODO( TASK_ID, TASK, CREATION_DATE ) VALUES ( NULL, ?, ? )",
        [request.form["task_details"], creation_date],
    )
    connection.commit()
    add_request("UPDATE_TODO_LIST")
    return redirect("tasks")


@app.route("/delete_task", methods=["GET"])
def delete_task() -> Response | str:
    """Deletes"""
    connection, cursor = get_connection()
    task_id = request.args.get("task_id", None)
    if task_id is None:
        return TASK_ID_IS_NONE_ERROR
    cursor.execute("DELETE FROM TODO WHERE TASK_ID = ?", [task_id])
    cursor.execute("DELETE FROM TASKS_LOG WHERE TASK_ID = ?", [task_id])
    connection.commit()
    add_request("UPDATE_TODO_LIST")
    return redirect("tasks")


@app.route("/task_done", methods=["GET"])
def mark_task_as_done() -> Response | str:
    """Move a task to the "Done" table"""
    connection, cursor = get_connection()
    task_id = request.args.get("task_id", None)
    if task_id is None:
        return TASK_ID_IS_NONE_ERROR
    current_date = strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute(
        "UPDATE TODO SET WORKING_ON = 'N', DONE = 'Y', DONE_AT = ? WHERE TASK_ID = ?",
        [current_date, task_id],
    )
    connection.commit()
    add_request("UPDATE_TODO_LIST")
    return redirect("tasks")


@app.route("/start_task", methods=["GET"])
def start_working_on_task() -> Response | str:
    """Create the banner to indicate a task is currently pending"""
    connection, cursor = get_connection()
    task_id = request.args.get("task_id", None)
    if task_id is None:
        return TASK_ID_IS_NONE_ERROR
    cursor.execute(
        "SELECT COUNT( 1 ) FROM TODO WHERE WORKING_ON = 'Y' AND TASK_ID <> ?", [task_id]
    )
    currently_working_on = cursor.fetchone()[0]
    if currently_working_on > 0:
        return render_template(
            "message.html",
            message="You're already working on another task!",
            type="warning",
        )
    creation_date = strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute("UPDATE TODO SET WORKING_ON = 'Y' WHERE TASK_ID = ?", [task_id])
    cursor.execute(
        "INSERT INTO TASKS_LOG( TASK_ID, START_AT ) VALUES ( ?, ? )",
        [task_id, creation_date],
    )
    connection.commit()
    add_request("UPDATE_TODO_LIST")
    return redirect("tasks")


@app.route("/stop_task", methods=["GET"])
def stop_working_on_task() -> Response | str:
    """Remove a pending task from the banner"""
    connection, cursor = get_connection()
    task_id = request.args.get("task_id", None)
    if task_id is None:
        return TASK_ID_IS_NONE_ERROR
    cursor.execute(
        "SELECT MAX( log_id ) FROM tasks_log WHERE TASK_ID = ? AND ENDED_AT IS NULL",
        [task_id],
    )
    current_task_log_id = cursor.fetchone()[0]
    current_date = strftime("%d-%m-%Y %H:%M:%S")
    cursor.execute("UPDATE TODO SET WORKING_ON = 'N' WHERE TASK_ID = ?", [task_id])
    cursor.execute(
        "UPDATE TASKS_LOG SET ENDED_AT = ? WHERE LOG_ID = ?",
        [current_date, current_task_log_id],
    )
    connection.commit()
    add_request("UPDATE_TODO_LIST")
    return redirect("tasks")


if __name__ == "__main__":
    app.debug = True
