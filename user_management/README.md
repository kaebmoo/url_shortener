# Flask-Base
 User Management from https://github.com/hack4impact/flask-base 
 Modified the code to be compatible with the new version of the library.
 
 URL Shorten Project

# Flask Application

This is a Flask application with various functionalities including database management, user authentication, and task queue processing.

## Features

- User and Role management
- URL shortening
- Redis queue for background tasks
- Database migrations
- Unit testing
- Fake data generation for development

## Configuration

The application uses a configuration system that supports multiple environments. The main configuration class is `Config`, with specific subclasses for different environments:

- `DevelopmentConfig`
- `TestingConfig`
- `ProductionConfig`
- `HerokuConfig`
- `UnixConfig`

### Environment Variables

The application uses several environment variables for configuration. These can be set in a `config.env` file in the root directory. Important variables include:

- `FLASK_CONFIG`: Determines which configuration to use (default is 'development')
- `SECRET_KEY`: Used for cryptographic operations
- `SHORTENER_HOST`: Host for the URL shortener service
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`: Email configuration
- `ADMIN_PASSWORD`, `ADMIN_EMAIL`: Admin account details
- `REDIS_URL`: URL for Redis connection
- `DATABASE_URL`: Main database URL
- `SHORTENER_DATABASE_URL`: Database URL for the URL shortener service

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

[Rest of the commands section remains the same]

## Running the Application

To run the application:
