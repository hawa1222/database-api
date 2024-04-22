# Database API

The Database API is a dynamic API built with FastAPI that simplifies interactions with a MySQL database. It provides endpoints for connecting to the database and creating, loading, fetching, and deleting tables.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Authentication](#authentication)
  - [Database Operations](#database-operations)
  - [User Operations](#user-operations)
  - [Table Operations](#table-operations)
  - [Data Operations](#data-operations)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

Before running the Database API, ensure you have the following software installed:
- Python (version 3.12)
- Poetry (version 1.8.2)
- MySQL (version 8.3.0)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/hawa1222/database-api.git
```
```bash
cd database-api
```

2. Install the project dependencies using Poetry:

```bash
poetry install
```

## Configuration

1. Create a `.env` file in the project root directory and provide the environment variables as specified in .env_template

2. Generate SSL certificate and key files (`cert.pem` and `key.pem`) and place them in the project root directory (optional).

## Usage

To start the Database API server, run the following command:

```bash
poetry run uvicorn app.main:app --reload
```

The API will be accessible at `http://localhost:8000/docs`.

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

## Project Structure

The project structure is organized as follows:

```plaintext
database_api/
├── .env
├── .gitignore
├── cert.pem
├── key.pem
├── logs/
│   └── logs.txt
├── poetry.lock
├── poetry.toml
├── pyproject.toml
├── README.md
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── permissions.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── crud.py
│   │   ├── database.py
│   │   └── models.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── create_admin.py
│       └── logging.py
│
└── tests/
    ├── __init__.py
    ├── api_test.py
    └── integration_testing.py
```

## Testing

The project includes unit tests and integration tests. To run the tests, use the following command:

```bash
poetry run pytest
```

## Logging

The Database API utilises logging to track important events and errors. Log files are stored in the `logs/` directory.

## License

This project is licensed under the [MIT License](LICENSE).