from sqlalchemy.future import select
from sqlalchemy import text
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Custom imports
from app.utils.logging import setup_logging
from app.schemas import schemas
from app.database import models

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logger
logger = setup_logging()

# ------------------------------
# Database CRUD Operations
# ------------------------------

async def create_database(db: AsyncSession, database: schemas.DatabaseCreate):
    """
    Create a new database.

    Args:
        db (AsyncSession): The database session.
        database (schemas.DatabaseCreate): The name of the database to create.

    Returns:
        dict: A dictionary containing a success or error message.

    Raises:
        HTTPException: If the database already exists or an error occurs during creation.
    """

    logger.info('curd.py create_database:')

    try:
        create_query = text(f"CREATE DATABASE {database.db_name}")
        await db.execute(create_query)
        await db.commit()
        message = f"Database '{database.db_name}' created successfully"
        logger.info(message)
        return {"message": message}
    
    except Exception as e:
        await db.rollback()
        if "database exists" in str(e).lower() or e.orig.args[0] == 1007:
            error_message = f"Database '{database.db_name}' already exists: {str(e.orig)}"
            logger.warning(error_message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
        else:
            error_message = f"Error creating database '{database.db_name}': {str(e)}"
            logger.error(error_message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)
        
# ------------------------------

async def create_db_user(db: AsyncSession, user: schemas.DBUserCreate):
    """
    Create a database user if it doesn't exist, or update the user's privileges if it already exists.

    Args:
        db (AsyncSession): The database session.
        user (schemas.DBUserCreate): The user object containing the host, username, password, 
        db_name, and privileges.

    Returns:
        dict: A dictionary containing a success or error message.

    Raises:
        HTTPException: If there is an error creating or updating the DB user.
    """

    logger.info('crud.py create_db_user:')

    try:
        # Check if the user already exists using a parameterized query
        result = await db.execute(
            text("SELECT User FROM mysql.user WHERE User = :username AND Host = :host"),
            {'username': user.username, 'host': user.host})
        if result.first():
            error_message = f"DB user '{user.username}' already exists"
            logger.warning(error_message)
            # User exists, update the user's privileges
            await set_user_privileges(db, user)
            return {"message": error_message}
        else:
            # Create the user if it doesn't exist
            await db.execute(
                text("CREATE USER :username@:host IDENTIFIED BY :password"),
                {'username': user.username, 'host': user.host, 'password': user.password})
            success_message = f"DB user '{user.username}' created successfully"
            logger.info(success_message)
            await set_user_privileges(db, user)
            return {"message": success_message}

    except Exception as e:
        await db.rollback()
        error_message = f"Error creating or updating DB user '{user.username}': {str(e.orig)}"
        logger.error(error_message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)

async def set_user_privileges(db: AsyncSession, user: schemas.DBUserCreate):
    """
    Sets the privileges for a user on a specific database.

    Args:
        db (AsyncSession): The database session.
        user (schemas.DBUserCreate): The user object containing the host, username, password, 
        db_name, and privileges.

    Returns:
        None, but commits the transaction.

    Raises:
        None
    """

    logger.info('crud.py set_user_privileges:')

    await db.execute(text(f"GRANT {user.privileges} ON {user.db_name}.* TO :username@:host"),
        {'username': user.username, 'host': user.host})
    await db.execute(text("FLUSH PRIVILEGES"))
    logger.info(f"DB user privilges set to '{user.privileges}'' on '{user.db_name}'")
    await db.commit()

# ------------------------------

async def create_table(db: AsyncSession, table_info: schemas.TableCreate):
    """
    Create a table in the database.

    Args:
        db (AsyncSession): The database session.
        table_info (schemas.TableCreate): table_name, db_name, and table_schema, 
        which contains the field names and data types / constraints.

    Returns:
        dict: A dictionary containing a success or error message.

    Raises:
        HTTPException: If the table already exists or if there is an error creating the table.
    """

    logger.info('crud.py create_table:')

    try:
        # Directly include the database name in the SQL statement
        db_tb_name = f"`{table_info.db_name}`.`{table_info.table_name}`"
        fields = table_info.table_schema
        # Generate the SQL query for creating the table
        create_table_query = generate_create_table_query(db_tb_name, fields)
        await db.execute(text(create_table_query))
        await db.commit()
        message=f"Table '{table_info.table_name}' created successfully in database '{table_info.db_name}'"
        logger.info(message)
        return {"message": message}
    
    except Exception as e:
        await db.rollback()
        if "already exists" in str(e).lower() or e.orig.args[0] == 1050:
            error_message = f"Table '{table_info.table_name}' already exists in database '{table_info.db_name}: {str(e.orig)}'"
            logger.warning(error_message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)
        else:
            error_message = f"Error creating table '{table_info.table_name}': {str(e.orig)}"
            logger.error(error_message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)

def generate_create_table_query(db_tb_name, fields):
    """
    Generate a SQL query to create a table in the database.

    Args:
        db_tb_name (str): The name of the table to be created.
        fields (dict): A dictionary containing the field names and their 
        corresponding data types / constraints.

    Returns:
        str: The SQL query to create the table.

    Example:
        >>> fields = {'id': 'INT', 'name': 'VARCHAR(255)', 'age': 'INT'}
        >>> generate_create_table_query('users', fields)
        'CREATE TABLE users (`id` INT, `name` VARCHAR(255), `age` INT)'
    """

    logger.info('crud.py generate_create_table_query:')

    # Build SQL CREATE TABLE statement
    field_definitions = ', '.join([f"`{name}` {type}" for name, type in fields.items()])
    query = f"CREATE TABLE {db_tb_name} ({field_definitions})"
    logger.info(f"Generated create table query")

    return query

async def get_table(db: AsyncSession, table_fetch: schemas.TableIdentify):
    """
    Fetches a table from the database.

    Args:
        db (AsyncSession): The database session.
        table_fetch (schemas.TableIdentify): The db_name and table_name to fetch.

    Returns:
        dict: A dictionary containing the table name and its data or an error message.

    Raises:
        HTTPException: If the table does not exist or an error occurs while fetching the table.
    """

    logger.info('crud.py get_table:')

    try:
        # Execute a query specifying the database directly
        query = f"SELECT * FROM `{table_fetch.db_name}`.`{table_fetch.table_name}`"
        result = await db.execute(text(query))
        table_data = [row._asdict() for row in result.fetchall()]
        message = f"Fetched table '{table_fetch.table_name}' from database '{table_fetch.db_name}'"
        logger.info(message)
        return {table_fetch.table_name: schemas.TableData(table_name=table_fetch.table_name, data=table_data)}
    
    except Exception as e:
        await db.rollback()
        if "doesn't exist" in str(e).lower():
            error_message = f"Table '{table_fetch.table_name}' does not exist in database '{table_fetch.db_name}': {str(e.orig)}"
            logger.error(error_message)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        else:
            error_message = f"Error fetching table '{table_fetch.table_name}': {str(e)}"
            logger.error(error_message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)

async def insert_data(db: AsyncSession, data_insert: schemas.TableData):
    """
    Insert data into a database table.

    Args:
        db (AsyncSession): The database session.
        data_insert (schemas.TableData): The db_name, table_name, and data to be inserted.

    Returns:
        dict: A dictionary containing the message with the number of records added and updated
        or an error message.

    Raises:
        HTTPException: If the table does not exist or if there is an error during data insertion.
    """

    logger.info('crud.py insert_data:')

    try:
        # Initialize counters for added and updated records
        added_count = 0
        updated_count = 0
        
        # Generate the SQL query for data insertion
        insert_query = generate_insert_query(data_insert.db_name, data_insert.table_name, list(data_insert.data[0].keys()))
        
        # Iterate over each row in the data
        for row in data_insert.data:
            # Prepare a dictionary of data for insertion
            data_dict = {key: (value if value is not None else None) for key, value in row.items()}
            # Execute the insert query with the prepared data tuple
            result = await db.execute(text(insert_query), data_dict)
            # Check the number of affected rows to determine if the row was added or updated
            if result.rowcount == 1:
                added_count += 1
            else:
                updated_count += 1
                
        # Commit the transaction to save changes
        await db.commit()
        message = (f"Data insertion completed for table '{data_insert.table_name}' in database '{data_insert.db_name}': " +
                   f"{added_count} records added, {updated_count} records updated")
        logger.info(message)
        # Return the number of records added and updated after completing the insertion process
        return {"message": message}
    
    except Exception as e:
        await db.rollback()
        if "doesn't exist" in str(e).lower() or e.orig.args[0] == 1146:
            error_message = f"Table '{data_insert.table_name}' does not exist in database '{data_insert.db_name}': {str(e.orig)}"
            logger.error(error_message)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        else:
            error_message = f"Error during data insertion: {str(e.orig)}"
            logger.error(error_message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)

def generate_insert_query(db_name: str, table_name: str, column_names: List[str]) -> str:
    """
    Generate an INSERT INTO SQL query with ON DUPLICATE KEY UPDATE clause.

    Args:
        db_name (str): The name of the database.
        table_name (str): The name of the table.
        column_names (List[str]): The list of column names.

    Returns:
        str: The complete INSERT INTO SQL query.

    Example:
        >>> generate_insert_query('mydb', 'mytable', ['col1', 'col2', 'col3'])
        "INSERT INTO `mydb`.`mytable` (col1, col2, col3) VALUES (:col1, :col2, :col3) ON DUPLICATE KEY UPDATE col1 = VALUES(col1), col2 = VALUES(col2), col3 = VALUES(col3)"
    """

    logger.info('crud.py generate_insert_query:')

    # Construct the column names and placeholders for the INSERT query
    columns = ', '.join(column_names)
    values_placeholders = ', '.join([':' + col for col in column_names])
    # Construct the ON DUPLICATE KEY UPDATE clause
    update_clause = ', '.join([f"{col} = VALUES({col})" for col in column_names])
    # Return the complete INSERT INTO SQL query
    query = f'''INSERT INTO `{db_name}`.`{table_name}` ({columns}) VALUES ({values_placeholders}) ON DUPLICATE KEY UPDATE {update_clause}'''
    logger.info(f"Generated insert query")

    return query

async def delete_table(db: AsyncSession, table_delete: schemas.TableIdentify):
    """
    Delete a table from the database.

    Args:
        db (AsyncSession): The database session.
        table_delete (schemas.TableIdentify): The db_name and table_name to delete.

    Returns:
        dict: A dictionary containing a success message or an error message.

    Raises:
        HTTPException: If the table does not exist or an error occurs during deletion.
    """

    logger.info('crud.py delete_table:')

    try:
        await db.execute(text(f"DROP TABLE {table_delete.db_name}.{table_delete.table_name}"))
        await db.commit()  # Commit right after dropping the table.
        message = f"Table '{table_delete.db_name}' deleted successfully from database '{table_delete.db_name}'"
        logger.info(message)
        return {"message": message}
    
    except Exception as e:
        await db.rollback()
        if "unknown table" in str(e).lower() or e.orig.args[0] in [1146, 1051]:
            error_message = f"Table '{table_delete.db_name}' does not exist in database '{table_delete.db_name}': {str(e.orig)}"
            logger.warning(error_message)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
        else:
            error_message = f"Error deleting table: {str(e.orig)}"
            logger.error(error_message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)

# ------------------------------
# Authentication and Authorisation
# ------------------------------

async def create_api_user(db: AsyncSession, user: schemas.UserCreate, hashed_password: str):
    """
    Create an API user in the database.

    Args:
        db (AsyncSession): The database session.
        user (schemas.UserCreate): The user object containing the username, password, and is_admin flag.
        hashed_password (str): The hashed password for the user.

    Returns:
        dict: A dictionary containing a success message or an error message.

    Raises:
        HTTPException: If there is an error creating the API user.
    """

    logger.info('crud.py create_api_user:')

    try:
        db_user = models.User(username=user.username, hashed_password=hashed_password, is_admin=user.is_admin)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        message = f"API user '{user.username}' created successfully"
        logger.info(message)
        return {"message": message}
    
    except Exception as e:
        db.rollback()
        error_message = f"Error creating API user '{user.username}': {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)

async def get_user_by_username(db: AsyncSession, username: str):
    """
    Retrieve a user from the database by their username.

    Args:
        db (AsyncSession): The database session.
        username (str): The username of the user to retrieve.

    Returns:
        User: The user object if found, None otherwise.

    Raises:
        HTTPException: If there is an error retrieving the user.

    """
    
    logger.info('crud.py get_user_by_username:')

    try:
        query = select(models.User).where(models.User.username == username)
        # this line queries the database for the user with the given username
        result = await db.execute(query)
        user = result.scalars().first()
        if not user:
            logger.info(f"API user '{username}' not found")
            return None

        logger.info(f"API user '{username}' details found")

        return user

    except Exception as e:
        await db.rollback()
        error_message = f"Error retrieving API user '{username}': {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message)

