from typing import List

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import auth_schemas, data_schemas

# Custom imports
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logger
logger = setup_logging()

# ------------------------------
# Database CRUD Operations
# ------------------------------


# CRUD function to create new database
async def create_database(db: AsyncSession, database: data_schemas.DatabaseCreate):
    """
    Create new database.

    Parameters:
        db (AsyncSession): database session.
        database (data_schemas.DatabaseCreate): name of database to create.

    Returns:
        dict: dictionary containing success or error message.

    Raises:
        HTTPException: If database already exists or error occurs.
    """

    logger.info("data_crud.py ---> create_database:")

    try:
        query = text(f"CREATE DATABASE {database.db_name}")  # Construct query
        await db.execute(query)  # Execute query
        await db.commit()  # Commit transaction

        message = f'Database "{database.db_name}" created successfully'
        logger.info(message)  # Log success message

        return {"message": message}  # Return success message

    except Exception as e:
        await db.rollback()  # Rollback transaction

        # Error message if database already exists
        if "database exists" in str(e).lower() or e.orig.Parameters[0] == 1007:
            error_message = f'Database "{database.db_name}" already exists: {str(e.orig)}'
            logger.warning(error_message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

        # Catch all other errors and log error message
        else:
            error_message = f'Error creating database "{database.db_name}": {str(e)}'
            logger.error(error_message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
            )


# ------------------------------


# CRUD function to create new database user
async def create_db_user(db: AsyncSession, user: auth_schemas.DBUserCreate):
    """
    Create database user if doesn't exist, or update user's privileges if
    already exists.

    Parameters:
        db (AsyncSession): database session.
        user (auth_schemas.DBUserCreate): user object containing host,
        username, password, db_name, and privileges.

    Returns:
        dict: dictionary containing success or error message.

    Raises:
        HTTPException: If there is error creating or updating DB user.
    """

    logger.info("data_crud.py ---> create_db_user:")

    try:
        result = await db.execute(
            text("""SELECT User FROM mysql.user WHERE
                 User = :username AND Host = :host"""),
            {"username": user.username, "host": user.host},
        )  # Construct & execute query: select user from mysql.user

        if result.first():  # Check first result to see if user exists
            error_message = f'DB user "{user.username}" already exists'
            logger.warning(error_message)  # Log warning message

            await set_user_privileges(db, user)  # Set user privileges

            return {"message": error_message}  # Return warning message

        else:
            await db.execute(
                text("CREATE USER :username@:host IDENTIFIED BY :password"),
                {
                    "username": user.username,
                    "host": user.host,
                    "password": user.password,
                },
            )  # Construct & execute query: create user

            success_message = f'DB user "{user.username}" created successfully'
            logger.info(success_message)  # Log success message

            await set_user_privileges(db, user)  # Set user privileges

            return {"message": success_message}  # Return success message

    except Exception as e:
        await db.rollback()  # Rollback transaction

        error_message = f"Error creating or updating DB user " f'"{user.username}": {str(e.orig)}'
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


# Function to create SQL query for setting user privileges
async def set_user_privileges(db: AsyncSession, user: auth_schemas.DBUserCreate):
    """
    Sets privileges for user on specific database.

    Parameters:
        db (AsyncSession): database session.
        user (auth_schemas.DBUserCreate): user object containing host,
        username, password, db_name, and privileges.

    Returns:
        None, but commits transaction.

    Raises:
        None
    """

    logger.info("data_crud.py ---> set_user_privileges:")

    # Set user privileges on specified database
    await db.execute(
        text(f"GRANT {user.privileges} ON {user.db_name}.* TO :username@:host"),
        {"username": user.username, "host": user.host},
    )  # Construct & execute query: grant privileges
    await db.execute(text("FLUSH PRIVILEGES"))  # Flush privileges
    await db.commit()  # Commit transaction

    logger.info(f'DB user privilges set to "{user.privileges}" ' f'on "{user.db_name}"')


# ------------------------------


# CRUD function to create new table in database
async def create_table(db: AsyncSession, table_info: data_schemas.TableCreate):
    """
    Create table in database.

    Parameters:
        db (AsyncSession): database session.
        table_info (data_schemas.TableCreate): table_name, db_name, and
        table_schema, which contains field names and dattypes/constraints.

    Returns:
        dict: dictionary containing success or error message.

    Raises:
        HTTPException: If table already exists or if error creating table.
    """

    logger.info("data_crud.py ---> create_table:")

    try:
        db_tb_name = f"`{table_info.db_name}`.`{table_info.table_name}`"
        fields = table_info.table_schema  # Create query parameters

        # Generate SQL query for creating table
        create_table_query = generate_create_table_query(db_tb_name, fields)
        await db.execute(create_table_query)  # Execute query
        await db.commit()  # Commit transaction

        message = (
            f'Table "{table_info.table_name}" created successfully '
            f'in database "{table_info.db_name}"'
        )
        logger.info(message)  # Log success message

        return {"message": message}  # Return success message

    except Exception as e:
        await db.rollback()  # Rollback transaction

        # Error message if table already exists
        if "already exists" in str(e).lower() or e.orig.Parameters[0] == 1050:
            error_message = (
                f'Table "{table_info.table_name}" already exists '
                f'in database "{table_info.db_name}": {str(e.orig)}'
            )
            logger.warning(error_message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
        else:
            # Catch all other errors and log error message
            error_message = f'Error creating table "{table_info.table_name}"' f": {str(e.orig)}"
            logger.error(error_message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
            )


# Function to generate SQL query to create table
def generate_create_table_query(db_tb_name, fields):
    """
    Generate SQL query to create table in database.

    Parameters:
        db_tb_name (str): name of table to be created.
        fields (dict): dictionary containing field names and their
        corresponding dattypes / constraints.

    Returns:
        str: SQL query to create table.

    Example:
        >>> fields = {'id': 'INT', 'name': 'VARCHAR(255)', 'age': 'INT'}
        >>> generate_create_table_query('users', fields)
        'CREATE TABLE users (`id` INT, `name` VARCHAR(255), `age` INT)'
    """

    logger.info("data_crud.py ---> generate_create_table_query:")

    # Build SQL CREATE TABLE statement with field definitions
    field_definitions = ", ".join([f"`{name}` {type}" for name, type in fields.items()])
    query = text(f"CREATE TABLE {db_tb_name} ({field_definitions})")

    logger.info("Generated create table query")  # Log success message

    return query  # Return SQL query


# ------------------------------


# CRUD function to fetch table from database
async def get_table(db: AsyncSession, table_fetch: data_schemas.TableIdentify):
    """
    Fetches table from database.

    Parameters:
        db (AsyncSession): database session.
        table_fetch (data_schemas.TableIdentify): db_name and table_name
        to fetch.

    Returns:
        dict: Dictionary containing table name and its dator error message.

    Raises:
        HTTPException: If table does not exist or
            error occurs while fetching table.
    """

    logger.info("data_crud.py ---> get_table:")

    try:
        db_name = table_fetch.db_name
        table_name = table_fetch.table_name
        query = text(f"SELECT * FROM `{db_name}`.`{table_name}`")
        result = await db.execute(query)  # Execute query
        # Fetch data, convert each row to dictionary, and store in list
        table_data = [row._asdict() for row in result.fetchall()]

        message = f'Fetched table "{table_name}" ' f'from database "{db_name}"'
        logger.info(message)  # Log success message

        return {
            table_name: data_schemas.TableData(
                db_name=db_name, table_name=table_name, data=table_data
            )
        }

    except Exception as e:
        await db.rollback()  # Rollback transaction

        # Error message if table does not exist
        if "doesn't exist" in str(e).lower():
            error_message = (
                f'Table "{table_name}" does not exist'
                f' in database "{db_name}":'
                f" {str(e.orig)}"
            )
            logger.error(error_message)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        else:
            # Catch all other errors and log error message
            error_message = f'Error fetching table "{table_name}"' f": {str(e)}"
            logger.error(error_message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
            )


# ------------------------------


# CRUD function to insert datinto table
async def insert_data(db: AsyncSession, data_insert: data_schemas.TableData):
    """
    Insert datinto database table.

    Parameters:
        db (AsyncSession): database session.
        data_insert (data_schemas.TableData): db_name, table_name, and data
        to be inserted.

    Returns:
        dict: dictionary containing message with number of
        records added and updated or an error message.

    Raises:
        HTTPException: If table does not exist or if there is an error
        during datinsertion.
    """

    logger.info("data_crud.py ---> insert_data:")

    try:
        # Initialise counters for added and updated records
        added_count = 0
        updated_count = 0

        # Generate SQL query for datinsertion
        insert_query = generate_insert_query(
            data_insert.db_name,
            data_insert.table_name,
            list(data_insert.data[0].keys()),
        )

        # Iterate over each row in data
        for row in data_insert.data:
            # Dict: column name, datfor insertion, replacing None with NULL
            data_dict = {key: (value if value is not None else None) for key, value in row.items()}
            # Execute insert query with prepared dattuple
            result = await db.execute(insert_query, data_dict)
            # Check no. affected rows to determine if row was added or updated
            if result.rowcount == 1:
                added_count += 1
            else:
                updated_count += 1

        await db.commit()  # Commit transaction after all datinserted

        message = (
            f"Datinsertion completed for table "
            f"{data_insert.table_name!r} in database "
            f"{data_insert.db_name!r}: {added_count} records added, "
            f"{updated_count} records updated, "
        )
        logger.info(message)

        return {"message": message}  # Return no. records added and updated

    except Exception as e:
        await db.rollback()  # Rollback transaction

        # Error message if table does not exist
        if "doesn't exist" in str(e).lower() or e.orig.Parameters[0] == 1146:
            error_message = (
                f'Table "{data_insert.table_name}" does not '
                f'exist in database "{data_insert.db_name}": '
                f"{str(e.orig)}"
            )
            logger.error(error_message)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        else:
            # Catch all other errors and log error message
            error_message = f"Error during datinsertion: {str(e.orig)}"
            logger.error(error_message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
            )


# Function to generate INSERT INTO SQL query + ON DUPLICATE KEY UPDATE clause
def generate_insert_query(db_name: str, table_name: str, column_names: List[str]) -> str:
    """
    Generate INSERT INTO SQL query with ON DUPLICATE KEY UPDATE clause.

    Parameters:
        db_name (str): name of database.
        table_name (str): name of table.
        column_names (List[str]): list of column names.

    Returns:
        str: complete INSERT INTO SQL query.

    Example:
        >>> generate_insert_query('mydb', 'mytable', ['col1', 'col2', 'col3'])
        "INSERT INTO `mydb`.`mytable` (col1, col2, col3) VALUES
        (:col1, :col2, :col3) ON DUPLICATE KEY UPDATE col1 = VALUES(col1),
        col2 = VALUES(col2), col3 = VALUES(col3)"
    """

    logger.info("data_crud.py ---> generate_insert_query:")

    # Construct column names and placeholders for INSERT query
    columns = ", ".join(column_names)
    values_placeholders = ", ".join([":" + col for col in column_names])

    update_clause = text(
        ", ".join([f"{col} = VALUES({col})" for col in column_names])
    )  # Construct ON DUPLICATE KEY UPDATE clause

    query = text(
        f"""INSERT INTO `{db_name}`.`{table_name}` ({columns}) VALUES(
        {values_placeholders}) ON DUPLICATE KEY UPDATE {update_clause}"""
    )  # Construct complete INSERT INTO SQL query

    logger.info("Generated insert query")  # Log success message

    return query  # Return SQL query


# ------------------------------


# CRUD function to delete table from database
async def delete_table(db: AsyncSession, table_delete: data_schemas.TableIdentify):
    """
    Delete table from database.

    Parameters:
        db (AsyncSession): database session.
        table_delete (data_schemas.TableIdentify): db_name and table_name
        to delete.

    Returns:
        dict: dictionary containing success message or error message.

    Raises:
        HTTPException: If table does not exist or error occurs.
    """

    logger.info("data_crud.py ---> delete_table:")

    try:
        query = text(
            f"DROP TABLE {table_delete.db_name}.{table_delete.table_name}"
        )  # SQL query to delete table
        await db.execute(query)  # Execute query
        await db.commit()  # Commit transaction
        message = (
            f'Table "{table_delete.db_name}" deleted successfully '
            f'from database "{table_delete.db_name}"'
        )
        logger.info(message)  # Log success message
        return {"message": message}  # Return success message

    except Exception as e:
        await db.rollback()  # Rollback transaction

        # Error message if table does not exist
        if "unknown table" in str(e).lower() or e.orig.Parameters[0] in [1146, 1051]:
            error_message = (
                f'Table "{table_delete.db_name}" does not exist '
                f'in database "{table_delete.db_name}": '
                f"{str(e.orig)}"
            )
            logger.warning(error_message)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)

        # Catch all other errors and log error message
        else:
            error_message = f"Error deleting table: {str(e.orig)}"
            logger.error(error_message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
            )
