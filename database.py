import asyncio
import os
import sqlite3

import discord

import bot_config

LOG_CHANNEL_ID = bot_config._get_int_env("DATABASE_LOG_CHANNEL_ID")


class Database:
    bot: discord.Bot | None = None
    # EXAMPLE_DB = "dbs/example.db"

    @classmethod
    def init(cls, bot: discord.Bot):
        cls.bot = bot

    @classmethod
    def _log(cls, message: str):
        try:
            if cls.bot is None:
                print(f"{message}")
                return

            channel = cls.bot.get_channel(cls.LOG_CHANNEL_ID)

            if channel:
                asyncio.run_coroutine_threadsafe(channel.send(message), cls.bot.loop)

            print(f"{message}")
        except Exception as e:
            print(f"{e}: here is the message that didn't get logged:\n\t{message}")

    @staticmethod
    def insert_into_db(db_path, table, **columns) -> bool:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        keys = ", ".join(columns.keys())
        placeholders = ", ".join(["?"] * len(columns))
        values = tuple(columns.values())
        new_lines = "\n".join(f"    {k}: {v!r}" for k, v in columns.items())

        try:
            cursor.execute(
                f"INSERT INTO {table} ({keys}) VALUES ({placeholders})", values
            )
            conn.commit()

            Database._log(f"**New entry in `{table}`**\n```\n{new_lines}\n```\n")

            return True
        except sqlite3.IntegrityError as e:
            Database._log(
                f"**New entry failed to insert in `{table}`**: {e}\n```\n{new_lines}\n```\n"
            )
            return False
        finally:
            conn.close()

    @staticmethod
    def update_field(db_path: str, table: str, row_id: int, field: str, value):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,))
        old_row = cursor.fetchone()
        col_names = [desc[0] for desc in cursor.description]
        old_dict = dict(zip(col_names, old_row)) if old_row else {}

        # Use parameterized query to avoid SQL injection
        query = f"UPDATE {table} SET {field} = ? WHERE id = ?"
        cursor.execute(query, (value, row_id))
        conn.commit()

        cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,))
        new_row = cursor.fetchone()
        new_dict = dict(zip(col_names, new_row)) if new_row else {}

        conn.close()

        old_lines = "\n".join(f"    {k}: {v!r}" for k, v in old_dict.items())
        new_lines = "\n".join(f"    {k}: {v!r}" for k, v in new_dict.items())

        log_message = f"**Updated `{table}`**\nBefore:\n```\n{old_lines}\n```\nAfter:\n```\n{new_lines}\n```"

        Database._log(log_message)

    @staticmethod
    def fetch_one_as_dict(
        db_path: str, table: str, where: str, params: tuple = ()
    ) -> dict | None:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = f"SELECT * FROM {table} WHERE {where} LIMIT 1"
        cursor.execute(query, params)
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        col_names = [desc[0] for desc in cursor.description]
        conn.close()

        return dict(zip(col_names, row))

    @staticmethod
    def fetch_all_as_dict_arr(
        db_path: str, table: str, where: str = "1=1", params: tuple = ()
    ) -> list[dict]:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        query = f"SELECT * FROM {table} WHERE {where}"
        cursor.execute(query, params)
        rows = cursor.fetchall()

        if not rows:
            conn.close()
            return []

        col_names = [desc[0] for desc in cursor.description]
        conn.close()

        return [dict(zip(col_names, row)) for row in rows]

    @staticmethod
    def delete_from_db(db_path: str, table: str, where: str, params: tuple = ()):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {table} WHERE {where}", params)
        rows = cursor.fetchall()
        col_names = [d[0] for d in cursor.description]

        query = f"DELETE FROM {table} WHERE {where}"
        cursor.execute(query, params)

        conn.commit()
        conn.close()

        if rows:
            msg_lines = [f"**Deleted from `{table}`**\n```\n"]
            for row in rows:
                row_dict = dict(zip(col_names, row))
                formatted_row = "\n".join(
                    f"    {k}: {v!r}" for k, v in row_dict.items()
                )
                msg_lines.append(formatted_row)
            Database._log("\n```\n".join(msg_lines))
        else:
            Database._log(
                f"Delete executed on `{table}` with no matches (where={where})"
            )

    @staticmethod
    def entry_exists(db_path: str, table: str, field: str, value) -> bool:
        return (
            Database.fetch_one_as_dict(db_path, table, f"{field} = ?", (value,))
            is not None
        )

    @staticmethod
    def execute(db_path: str, query: str, params: tuple = ()) -> list[tuple]:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return rows


def setup_db(db_name, table_schemas):
    conn = sqlite3.connect(db_name)
    conn.close()

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    for schema in table_schemas:
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {schema['name']} ({schema['columns']})"
        )
    conn.commit()
    conn.close()


# Add new fields to existing tables
NEW_FIELDS = {
    # "example_table": [
    #     ("new_field", "TEXT DEFAULT NULL")
    # ],
}


def apply_schema_updates(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for table, new_columns in NEW_FIELDS.items():
        # skip tables that don't exist
        c.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        )
        if not c.fetchone():
            print(f"Table '{table}' not found, skipping.")
            continue

        # get existing columns
        c.execute(f"PRAGMA table_info({table})")
        existing = [row[1] for row in c.fetchall()]

        # add any missing columns
        for name, coltype in new_columns:
            if name not in existing:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {name} {coltype}")

    conn.commit()
    conn.close()


os.makedirs("dbs", exist_ok=True)
# setup_db(
#     Database.EXAMPLE_DB,
#     [
#         {
#             "name": "example_table",
#             "columns": "id INTEGER PRIMARY KEY, name TEXT"
#         }
#     ],
# )

# apply_schema_updates(Database.EXAMPLE_DB)
