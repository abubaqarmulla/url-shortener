# Scalable URL Shortener

A RESTful URL-shortening service built with Python, FastAPI, PostgreSQL, Redis, and Docker. This project demonstrates backend API development, authentication, caching, analytics, rate limiting, and containerization.

## Features

- User registration and JWT-based authentication
- Create, list, and delete shortened URLs
- Unique short codes
- URL expiration support
- Redis caching for URL redirects
- Click analytics and periodic synchronization
- Pagination for URL listings
- Redis-backed rate limiting
- PostgreSQL database with SQLAlchemy
- Alembic database migrations
- Docker Compose development environment
- Interactive API documentation with Swagger UI
- Automated tests using Pytest

## Tech Stack

- **Language:** Python
- **API Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM and Migrations:** SQLAlchemy, Alembic
- **Caching and Rate Limiting:** Redis
- **Authentication:** JWT
- **Containerization:** Docker, Docker Compose
- **Testing:** Pytest

## Project Structure

```text
url-shortener/
├── app/
│   ├── api/
│   ├── cache/
│   ├── core/
│   ├── database/
│   ├── schemas/
│   └── services/
├── migrations/
├── scripts/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python
- Docker Desktop
- Docker Compose

### 1. Configure environment variables

Create a local `.env.docker` file containing the following variables. Replace the placeholders with values matching your local PostgreSQL configuration.

```env
DATABASE_URL=postgresql+psycopg://<db-user>:<db-password>@postgres:5432/<db-name>
SECRET_KEY=<your-long-random-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_URL=redis://redis:6379
```

The PostgreSQL credentials and database name must match the PostgreSQL service configuration in `docker-compose.yml`.

### 2. Start the application

Run these commands from the project root:

```bash
docker compose up -d --build
docker compose ps
```

### 3. Verify the application

```bash
curl -i http://127.0.0.1:8000/health
```

The application should return an HTTP 200 response when healthy.

### 4. Explore the API

- **Swagger UI:** http://127.0.0.1:8000/docs
- **OpenAPI schema:** http://127.0.0.1:8000/openapi.json

### 5. Stop the application

```bash
docker compose down
```

To remove database and Redis volumes as well, use `docker compose down -v`. This permanently deletes the data stored in those volumes.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a user |
| POST | `/auth/login` | Log in and obtain an access token |
| GET | `/auth/me` | Retrieve the current user's profile |
| POST | `/urls` | Create a shortened URL |
| GET | `/urls` | List the authenticated user's URLs |
| DELETE | `/urls/{id}` | Delete an owned URL |
| GET | `/{short_code}` | Redirect to the original URL |
| GET | `/urls/{id}/analytics` | Retrieve URL analytics |
| GET | `/health` | Application health check |

Protected endpoints require a valid bearer token. Refer to Swagger UI for request schemas and endpoint details.

## Running Tests

Activate your Python virtual environment, install the project dependencies, and run:

```bash
pip install -r requirements.txt
pytest -v
```

The latest recorded test run completed with **23 passing tests**.

## Security

- Never commit `.env`, `.env.docker`, passwords, API keys, or private keys.
- Use a strong, unique secret key outside local development.
- Review development credentials in Docker configuration before publishing or deploying.
- Configure production secrets and infrastructure separately.
- Cloud deployment is planned and has not yet been completed.

## Future Improvements

- AWS deployment
- Production-grade secret management
- Additional reliability tests for analytics synchronization
- CI pipeline for automated testing

## License

No license has been selected yet. Add a `LICENSE` file if you intend to permit others to reuse this project.
