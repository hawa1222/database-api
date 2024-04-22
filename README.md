# Database API

The Database API is a dynamic API built with FastAPI that simplifies interactions with a MySQL database. It provides endpoints for connecting to the database and creating, loading, fetching, and deleting tables.

## Project Objectives

- Develop a dynamic FastAPI to simplify MySQL database interactions
- Implement secure authentication and role-based access control using OAuth2 and JWT
- Follow best practices for project structure and logging
- Optimize database operations with asynchronous programming using SQLAlchemy and asyncio
- Provide comprehensive API documentation and usage examples

## Project Architecture

The project consists of the following components:

- FastAPI: A Python web framework for building APIs. It serves as the main entry point for the API and handles incoming requests and outgoing responses.

- Authentication and Authorisation: The API utilises OAuth2 with JWT (JSON Web Tokens) for secure authentication and authorisation. It implements role-based access control to differentiate between admin and non-admin users.

- Database (MySQL): The API interacts with a MySQL database for storing and retrieving data. It provides endpoints for creating databases, tables, and performing CRUD operations on the data.

- SQLAlchemy: A SQL toolkit and Object-Relational Mapping (ORM) library for Python. It is used to define the database models, establish connections, and perform database operations asynchronously.

- Pydantic: A Python library for data validation and settings management using Python type annotations. It is used to define and validate request and response models, ensuring data integrity and consistency.

- Logging: The project incorporates logging to track important events, errors, and system behavior. Log files are stored in the `logs/` directory.

- Packaging and Dependency Management: The project uses Poetry, a modern Python packaging and dependency management tool.


## Prerequisites

Before running the Database API, ensure you have the following software installed:
- Python (version 3.12)
- Poetry (version 1.8.2)
- MySQL (version 8.3.0)

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/hawa1222/database-api.git
   ```

2. Navigate to the project directory:
   ```
   cd database-api
   ```

3. Install the project dependencies using Poetry:
   ```bash
   poetry install
   ```
3. Create a `.env` file in the project root directory and provide the environment variables as specified in `.env_template`.

4. Generate SSL certificate and key files (`cert.pem` and `key.pem`) and place them in the project root directory (optional).

## Usage

To start the Database API server, run the following command:

```bash
poetry run uvicorn app.main:app --reload
```

The API will be accessible at [http://localhost:8000/docs](http://localhost:8000/docs/).

### Authentication

The Database API uses OAuth2 with JWT for authentication. To access protected endpoints, you need to obtain an access token by providing valid credentials.

- `POST /register-api-user`: Register a new API user (admin only).
- `POST /get-token`: Obtain an access token by providing API user credentials.

### Database Operations

- `POST /create-database`: Create a new database.

### User Operations

- `POST /create-db-user`: Create a new database user (admin only).

### Table Operations

- `POST /create-table`: Create a new table in a database.
- `GET /get-table/{db_name}/{table_name}`: Get data from a table (admin only).
- `DELETE /delete-table/{db_name}/{table_name}`: Delete a table from a database (admin only).

### Data Operations

- `POST /insert-data`: Insert data into a table (admin only).

For detailed information about request and response formats, refer to the API documentation.

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.
