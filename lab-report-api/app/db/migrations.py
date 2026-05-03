from sqlalchemy import text


def _get_columns(connection, table_name: str) -> set[str]:
    rows = connection.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return {row["name"] for row in rows}


def _add_column_if_missing(
    connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    existing_columns = _get_columns(connection, table_name)
    if column_name not in existing_columns:
        connection.execute(
            text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
        )


def run_startup_migrations(engine) -> None:
    with engine.begin() as connection:
        _add_column_if_missing(connection, "users", "username", "VARCHAR")
        _add_column_if_missing(connection, "users", "password_hash", "VARCHAR")

        _add_column_if_missing(connection, "test_records", "report_number", "VARCHAR")
        _add_column_if_missing(connection, "test_records", "created_by_user_id", "INTEGER")
        _add_column_if_missing(connection, "test_records", "patient_phone", "VARCHAR")
        _add_column_if_missing(connection, "test_records", "referring_doctor", "VARCHAR")

        _add_column_if_missing(connection, "test_templates", "created_by_user_id", "INTEGER")
