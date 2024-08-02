import math

from fastapi import HTTPException
from fastapi import status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import auth_schemas
from app.schemas import data_schemas
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# Database CRUD Operations
# ------------------------------


async def create_database(db: AsyncSession, database: data_schemas.DatabaseCreate):
    """
    Create new database.

    Parameters:
        db (AsyncSession): Async database session.
        database (Pydantic model): Database object containing db_name.

    Returns:
        dict: Dictionary containing success message.

    Raises:
        HTTPException (400): If database already exists.
        HTTPException (500): If error creating database.
    """

    logger.debug("Creating database...")

    try:
        create_db_query = text(f"CREATE DATABASE {database.db_name}")
        await db.execute(create_db_query)
        await db.commit()

        message = f"Database '{database.db_name}' created successfully"
        logger.info(message)

        return {"message": message}

    except Exception as e:
        await db.rollback()

        if "1007" in str(e):
            error_message = f"Database '{database.db_name}' already exists"
            logger.warning(error_message + f": {str(e.orig)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

        else:
            error_message = f"Error occurred creating database '{database.db_name}'"
            logger.error(error_message + f": {str(e.orig)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
            )


async def create_db_user(db: AsyncSession, user: auth_schemas.DBUserCreate):
    """
    Create database user if doesn't exist, or update user's privileges if
    already exists.

    Parameters:
        db (AsyncSession): Async database session.
        user (Pydantic model): Database user object containing host,
        username, password, db_name, and privileges.

    Returns:
        dict: Dictionary containing sucess message.

    Raises:
        HTTPException (500): If error creating or updating DB user.
    """

    logger.debug("Creating database user...")

    try:
        create_query = text("""SELECT User FROM mysql.user WHERE
                                 User = :username AND Host = :host""")
        result = await db.execute(create_query, {"username": user.username, "host": user.host})

        if result.first():
            error_message = f"DB user '{user.username}' already exists"
            logger.warning(error_message)
            await set_user_privileges(db, user)

            return {"message": error_message}

        else:
            create_query = text("CREATE USER :username@:host IDENTIFIED BY :password")
            await db.execute(
                create_query,
                {"username": user.username, "host": user.host, "password": user.password},
            )
            success_message = f"DB user '{user.username}' created successfully"
            logger.info(success_message)
            await set_user_privileges(db, user)

            return {"message": success_message}

    except Exception as e:
        await db.rollback()
        error_message = f"Error occurred creating DB user '{user.username}'"
        logger.error(error_message + f": {str(e.orig)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


async def set_user_privileges(db: AsyncSession, user: auth_schemas.DBUserCreate):
    """
    Sets privileges for user on specific database.

    Parameters:
        db (AsyncSession): Async database session.
        user (Pydantic model): User object containing host,
        username, password, db_name, and privileges.

    Returns:
        None, but commits transaction.

    Raises:
        None
    """

    logger.debug("Setting user privileges...")

    create_query = text(f"GRANT {user.privileges} ON {user.db_name}.* TO :username@:host")
    await db.execute(create_query, {"username": user.username, "host": user.host})
    await db.execute(text("FLUSH PRIVILEGES"))
    await db.commit()

    logger.debug(f"DB user privileges set to '{user.privileges}' on '{user.db_name}'")


async def create_table(db: AsyncSession, table_info: data_schemas.TableCreate):
    """
    Create table in database.

    Parameters:
        db (AsyncSession): Async database session.
        table_info (Pydantic model): Table object containing db_name,
        table_name, and table_schema, which contains field names and data types/constraints.

    Returns:
        dict: Dictionary containing success message.

    Raises:
        HTTPException (400): If table already exists.
        HTTPException (500): If error creating table.
    """

    logger.debug("Creating table...")

    try:
        db_tb_name = f"`{table_info.db_name}`.`{table_info.table_name}`"
        fields = table_info.table_schema  # Create query parameters

        create_table_query = generate_create_table_query(db_tb_name, fields)
        await db.execute(create_table_query)
        await db.commit()

        message = (
            f"Table '{table_info.table_name}' created successfully "
            f"in database '{table_info.db_name}'"
        )
        logger.info(message)

        return {"message": message}

    except Exception as e:
        await db.rollback()

        if "1050" in str(e).lower():
            error_message = f"Table '{table_info.table_name}' already exists in database '{table_info.db_name}'"
            logger.warning(error_message + f": {str(e.orig)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
        else:
            error_message = f"Error occurred creating table '{table_info.table_name}'"
            logger.error(error_message + f": {str(e.orig)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
            )


def generate_create_table_query(db_tb_name, fields):
    """
    Generate SQL query to create table in database.

    Parameters:
        db_tb_name (str): Name of table to be created.
        fields (dict): Dictionary containing field names and their
        corresponding data types/constraints.

    Returns:
        str: SQL query to create table.

    Example:
        >>> fields = {"id": "INT", "name": "VARCHAR(255)", "age": "INT"}
        >>> generate_create_table_query("users", fields)
        'CREATE TABLE users (`id` INT, `name` VARCHAR(255), `age` INT)'
    """

    logger.debug("Generating create table query...")

    field_definitions = ", ".join(
        [f"`{name}` {type}" for name, type in fields.items()]
    )  # Format field names and data types/constraints
    query = text(f"CREATE TABLE {db_tb_name} ({field_definitions})")

    logger.debug("Generated create table query")

    return query


async def get_table(db: AsyncSession, table_fetch: data_schemas.TableIdentify):
    """
    Fetches table from database.

    Parameters:
        db (AsyncSession): Async database session.
        table_fetch (Pydantic model): Table object containing db_name and table_name

    Returns:
        dict: Dictionary containing table name and data.

    Raises:
        HTTPException (404): If table does not exist.
        HTTPException (500): If error fetching table.
    """

    logger.debug("Fetching table...")

    try:
        db_name = table_fetch.db_name
        table_name = table_fetch.table_name
        query = text(f"SELECT * FROM `{db_name}`.`{table_name}`")
        result = await db.execute(query)
        table_data = [
            row._asdict() for row in result.fetchall()
        ]  # Fetch data, convert each row to dictionary, and store in list

        message = f"Fetched table '{table_name}' " f"from database '{db_name}'"
        logger.info(message)

        return {
            table_name: data_schemas.TableData(
                db_name=db_name, table_name=table_name, data=table_data
            )
        }

    except Exception as e:
        await db.rollback()

        if "doesn't exist" in str(e).lower():
            error_message = f"Table '{table_name}' does not exist in database '{db_name}'"
            logger.error(error_message + f": {str(e.orig)}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        else:
            error_message = f"Error occurred fetching table '{table_name}'"
            logger.error(error_message + f": {str(e.orig)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
            )


def handle_nan_values(row):
    """
    Handle NaN and None values in row of data.

    Parameters:
        row (Dict[str, Any]): Dictionary representing a row of data.

    Returns:
        Dict[str, Any]: Row with NaN and None values handled.
    """
    return {
        key: (None if value is None or (isinstance(value, float) and math.isnan(value)) else value)
        for key, value in row.items()
    }


async def insert_data(db: AsyncSession, data_insert: data_schemas.TableData):
    """
    Insert data into database table.

    Parameters:
        db (AsyncSession): Async database session.
        data_insert (Pydantic model): TableData object containing db_name,
        table_name, and data

    Returns:
        dict: Dictionary containing message with number of
        records added/unchanged and updated.

    Raises:
        HTTPException (404): If table does not exist.
        HTTPException (500): If error inserting data.
    """

    logger.debug("Inserting data into table...")

    try:
        added_count = 0  # Counter for no. records added
        updated_count = 0  # Counter for no. records updated

        insert_query = generate_insert_query(
            data_insert.db_name, data_insert.table_name, list(data_insert.data[0].keys())
        )

        for row in data_insert.data:  # Iterate over each row in data
            data_dict = handle_nan_values(row)  # Handle NaN values and None

            # Execute insert query with prepared data tuple
            result = await db.execute(insert_query, data_dict)
            # Check no. affected rows to determine if row was added or updated
            if result.rowcount == 1:
                added_count += 1
            else:
                updated_count += 1

        await db.commit()

        message = (
            f"Data insertion completed for table '{data_insert.table_name}' in database "
            f"'{data_insert.db_name}': {added_count} records added or unchanged, {updated_count} records updated"
        )
        logger.info(message)

        return {"message": message}  # Return no. records added and updated

    except Exception as e:
        await db.rollback()

        if "1146" in str(e).lower():
            error_message = f"Table '{data_insert.table_name}' does not exist in database '{data_insert.db_name}'"
            logger.error(error_message + f": {str(e.orig)}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        else:
            error_message = f"Error occurred inserting data into table '{data_insert.table_name}'"
            logger.error(error_message + f": {str(e.orig)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
            )


def generate_insert_query(db_name: str, table_name: str, column_names: list[str]) -> str:
    """
    Generate INSERT INTO SQL query with ON DUPLICATE KEY UPDATE clause.

    Parameters:
        db_name (str): Name of database.
        table_name (str): Name of table.
        column_names (List[str]): List of column names.

    Returns:
        str: complete INSERT INTO SQL query.

    Example:
        >>> generate_insert_query("mydb", "mytable", ["col1", "col2", "col3"])
        "INSERT INTO `mydb`.`mytable` (col1, col2, col3) VALUES
        (:col1, :col2, :col3) ON DUPLICATE KEY UPDATE col1 = VALUES(col1),
        col2 = VALUES(col2), col3 = VALUES(col3)"
    """

    logger.debug("Generating insert query...")

    columns = ", ".join(column_names)  # Concatenate column names
    values_placeholders = ", ".join(
        [":" + col for col in column_names]
    )  # Construct placeholders for values

    update_clause = text(
        ", ".join([f"{col} = VALUES({col})" for col in column_names])
    )  # Construct ON DUPLICATE KEY UPDATE clause

    query = text(
        f"""INSERT INTO `{db_name}`.`{table_name}` ({columns}) VALUES(
        {values_placeholders}) ON DUPLICATE KEY UPDATE {update_clause}"""
    )  # Construct complete INSERT INTO SQL query

    logger.debug("Generated insert query")

    return query


async def delete_table(db: AsyncSession, table_delete: data_schemas.TableIdentify):
    """
    Delete table from database.

    Parameters:
        db (AsyncSession): Async database session.
        table_delete (Pydantic model): Table object containing db_name and table_name.

    Returns:
        dict: Dictionary containing success message.

    Raises:
        HTTPException: (404): If table does not exist.
        HTTPException: (500): If error deleting table.
    """

    logger.debug("Deleting table...")

    try:
        create_query = text(f"DROP TABLE {table_delete.db_name}.{table_delete.table_name}")
        await db.execute(create_query)
        await db.commit()
        message = (
            f"Table '{table_delete.db_name}' deleted successfully "
            f"from database '{table_delete.db_name}'"
        )
        logger.info(message)
        return {"message": message}

    except Exception as e:
        await db.rollback()

        if "1146" in str(e).lower() or "1051" in str(e).lower():
            error_message = f"Table '{table_delete.db_name}' does not exist in database '{table_delete.db_name}'"
            logger.warning(error_message + f": {str(e.orig)}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)

        else:
            error_message = f"Error occurred deleting table '{table_delete.db_name}'"
            logger.error(error_message + f": {str(e.orig)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
            )
