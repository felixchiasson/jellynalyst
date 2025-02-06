## Deployment with Docker

### Prerequisites
- Docker
- Docker Compose

### Steps to deploy

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your actual configuration values

3. Build and start the containers:
   ```bash
   docker compose up -d --build
   ```

4. Run database migrations:
   ```bash
   docker compose exec web alembic upgrade head
   ```

5. Access the application at http://localhost:8000

### Useful commands

- View logs:
  ```bash
  docker compose logs -f
  ```

- Restart services:
  ```bash
  docker compose restart
  ```

- Stop all services:
  ```bash
  docker compose down
  ```

- Stop and remove all data (including database):
  ```bash
  docker compose down -v
  ```
```

To deploy the application:

1. **Build and start the containers**:
```bash
docker compose up -d --build
