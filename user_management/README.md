# Flask-Base
 User Management from https://github.com/hack4impact/flask-base 
 Modified the code to be compatible with the new version of the library.
 
 URL Shorten Project

# Flask Application

This is a Flask application with various functionalities including database management, user authentication, URL shortening, and task queue processing.

## Features

- User and Role management
- URL shortening
- Redis queue for background tasks
- Database migrations
- Unit testing
- Fake data generation for development
- Multiple environment configurations (Development, Testing, Production, Heroku, Unix)
- Email support
- Analytics integration (Google Analytics, Segment)
- Error tracking with Raygun

## Configuration

The application uses a flexible configuration system that supports multiple environments. The main configuration class is `Config`, with specific subclasses for different environments:

- `DevelopmentConfig`
- `TestingConfig`
- `ProductionConfig`
- `HerokuConfig`
- `UnixConfig`

### Environment Variables

Key configuration variables can be set in a `config.env` file in the root directory or as environment variables. Important variables include:

- `FLASK_CONFIG`: Determines which configuration to use (default is 'development')
- `SECRET_KEY`: Used for cryptographic operations
- `SHORTENER_HOST`: Host for the URL shortener service
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`: Email configuration
- `ADMIN_PASSWORD`, `ADMIN_EMAIL`: Admin account details
- `REDIS_URL`: URL for Redis connection
- `DATABASE_URL`: Main database URL
- `SHORTENER_DATABASE_URL`: Database URL for the URL shortener service
- `GOOGLE_ANALYTICS_ID`: Google Analytics tracking ID
- `SEGMENT_API_KEY`: Segment API key
- `RAYGUN_APIKEY`: Raygun API key for error tracking

### Database Configuration

The application uses SQLAlchemy and supports multiple database bindings:

- Main database: Configured via `SQLALCHEMY_DATABASE_URI`
- Shortener database: Configured via `SQLALCHEMY_BINDS['shortener_db']`

Different database URLs are used for development, testing, and production environments.

## Setup

1. Create a `config.env` file in the root directory and set the necessary environment variables.
2. Set the `FLASK_CONFIG` environment variable to choose the configuration (options: development, testing, production, heroku, unix).
3. Install the required dependencies (listed in `requirements.txt`).

## Commands

The application provides several CLI commands:

- `flask test`: Run unit tests
- `flask recreate_db`: Recreate the database (use with caution in production)
- `flask add-fake-data`: Add fake data to the database
- `flask setup_dev`: Set up for local development
- `flask setup_prod`: Set up for production
- `flask run_worker`: Start the RQ worker for background tasks
- `flask format`: Run code formatters (isort and yapf)

## Database Models

The application uses SQLAlchemy for database operations. Models include:

- User
- Role
- ShortenedURL

## Running the Application

To run the application:
The application will use the configuration specified by the `FLASK_CONFIG` environment variable, defaulting to 'development' if not set.

## Development

For development:

1. Set `FLASK_CONFIG=development` in your environment or `config.env` file.
2. Set up the development environment: `flask setup_dev`
3. Add fake data if needed: `flask add-fake-data`
4. Run the application: `python app.py`

Remember to run `flask format` before committing changes to ensure consistent code style.

## Production

For production deployment:

1. Ensure all necessary environment variables are set, especially `SECRET_KEY`.
2. Set `FLASK_CONFIG=production`.
3. Run `flask setup_prod` to set up the production environment.
4. Use a production WSGI server like Gunicorn to run the application.

## Testing

Run the test suite using:
This will discover and run all tests in the `tests` directory.

## Background Tasks

The application uses Redis Queue (RQ) for handling background tasks. To start a worker:
Ensure Redis is running and `REDIS_URL` is correctly set.

## Logging

In Unix environments, the application can log to syslog. This is automatically set up when using the `UnixConfig`.

## Error Tracking

Raygun is integrated for error tracking in production. Ensure `RAYGUN_APIKEY` is set in your production environment.
