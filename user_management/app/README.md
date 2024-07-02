
# URL Shortener with User Management

This project is a URL shortener web application with user management functionalities, built using Flask. It includes features such as user registration, login, email notifications, and URL shortening.

## Features

- User registration and authentication
- Email notifications
- URL shortening
- Asset pipeline management
- SSL configuration
- Task queue management with Redis Queue (RQ)

## Project Structure

- `assets/`: Contains CSS and JavaScript assets.
- `app/`: Main application folder containing blueprints for different modules.
  - `main/`: Main application routes.
  - `account/`: User account management routes.
  - `admin/`: Admin panel routes.
  - `url/`: URL shortening routes.
- `config/`: Configuration files for different environments.
- `templates/`: Jinja2 templates for rendering HTML pages.
- `utils/`: Utility functions.

## Installation

### Prerequisites

- Python 3.6+
- Flask
- Flask-Assets
- Flask-Compress
- Flask-Login
- Flask-Mail
- Flask-RQ2
- Flask-SQLAlchemy
- Flask-WTF
- Redis (for task queue management)

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/kaebmoo/url_shortener.git
   cd url_shortener/user_management/app
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   ```bash
   export FLASK_CONFIG=development
   ```

5. Initialize the database:

   ```bash
   flask db upgrade *** not sure
   ```

6. Run the application:

   ```bash
   flask run *** not sure
   web: gunicorn manage:app
   worker: python -u manage.py run_worker
   ```

## Configuration

The application can be configured using environment variables or by modifying the `config.py` file. The available configurations are:

- `development`
- `testing`
- `production`

## Usage

After setting up and running the application, you can access it in your web browser at `http://127.0.0.1:5000/`. You can register a new user, log in, and start shortening URLs.

## Task Queue

The application uses Redis Queue (RQ) for background task processing. To start a worker, run the following command in a separate terminal:

```bash
redis-server
rq worker --with-scheduler
```

## SSL Configuration

For production environments, SSL is configured if the platform supports it. Ensure to set `SSL_DISABLE` to `False` in the configuration.

## Acknowledgments

This project is adapted from the [flask-base](https://github.com/hack4impact/flask-base) project by Hack4Impact. 

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Additional Resources

- [Flask](https://flask.palletsprojects.com/)
- [Redis Queue (RQ)](https://python-rq.org/)
- [Flask-Assets](https://flask-assets.readthedocs.io/en/latest/)
- [Flask-Compress](https://github.com/colour-science/flask-compress)
- [Flask-Login](https://flask-login.readthedocs.io/en/latest/)
- [Flask-Mail](https://pythonhosted.org/Flask-Mail/)
- [Flask-RQ2](https://flask-rq2.readthedocs.io/en/latest/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [Flask-WTF](https://flask-wtf.readthedocs.io/en/stable/) 
