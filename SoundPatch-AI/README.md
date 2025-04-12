# SoundPatch API

A FastAPI-based backend application for SoundPatch.

## Project Structure

```
SoundPatch-AI/
├── app/
│   ├── core/
│   │   └── config.py         # Application configuration
│   ├── models/
│   │   └── message.py        # Pydantic models
│   ├── routes/
│   │   └── message.py        # API routes
│   └── main.py              # Main application file
├── run.py                   # Application runner
├── requirements.txt         # Project dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore          # Docker ignore file
└── README.md              # This file
```

## Setup

### Local Development

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Docker Development

1. Build and run the development container:
```bash
docker-compose build --target development
docker-compose up
```

2. For production:
```bash
docker-compose build --target production
docker-compose up
```

You can also set environment variables:
```bash
ENVIRONMENT=development DEBUG=true docker-compose up
```

## Running the Application

### Local Development

The application can be run in two modes:

#### Development Mode
```bash
python run.py --env development
```
This will run the application with:
- Hot reload enabled
- Debug mode on
- Detailed logging

#### Production Mode
```bash
python run.py --env production
```
This will run the application with:
- Multiple workers (4)
- Production-optimized settings
- Info-level logging

### Docker

The application can be run using Docker Compose:

```bash
# Development
docker-compose up --build

# Production
ENVIRONMENT=production docker-compose up --build
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:
- Interactive API docs (Swagger UI): `http://localhost:8000/docs`
- Alternative API docs (ReDoc): `http://localhost:8000/redoc`

## Available Endpoints

- `GET /`: Welcome message
- `GET /health`: Health check endpoint
- `POST /api/v1/message`: Create a new message
  - Request body:
    ```json
    {
        "content": "Your message here",
        "sender": "Optional sender name"
    }
    ```

## Configuration

The application uses environment variables for configuration. You can create a `.env` file in the root directory with the following variables:

```env
APP_NAME=SoundPatch API
APP_DESCRIPTION=A FastAPI backend for SoundPatch application
APP_VERSION=1.0.0
DEBUG=false
API_PREFIX=/api/v1
```

When using Docker, these environment variables can be set in the `docker-compose.yml` file or passed as environment variables when running the container. 