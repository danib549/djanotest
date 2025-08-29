# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based web application called "Script Creator" that manages automation scripts with versioning, encryption, and multi-project/multi-user support. The application uses Bootstrap for UI styling and HTMX for dynamic frontend interactions.

## Core Architecture

### Django Application Structure
- **Main Django Project**: `script_creator/` - Contains Django settings, URLs, and WSGI configuration
- **Primary App**: `automation/` - Main application module containing all business logic
  - Models define `Project` and `Script` entities with encryption support via `cryptography.fernet`
  - Views handle script creation, editing, version management, and user authentication
  - Custom managers in `script_db_manager.py` handle dynamic table creation for script versions per project
  - Session-based data management through `seasion_data_manager.py`

### Key Components
- **Script Storage**: Scripts are saved as encrypted `.ScriptQ` files in `media/scripts/project_[id]/`
- **Dynamic Database Tables**: Each project gets its own script version table created dynamically
- **Frontend**: Uses Bootstrap CSS framework and HTMX for dynamic partial template updates
- **Authentication**: Built-in Django authentication with login/logout redirects configured

## Development Commands

### Running the Development Server
```bash
python manage.py runserver
# or use the provided batch file on Windows:
./start.bat
```

### Database Management
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### Static Files
```bash
# Collect static files (for production)
python manage.py collectstatic
```

## Required Dependencies

The project requires the following Python packages:
- Django 5.1+
- cryptography (for Fernet encryption)

Install dependencies:
```bash
pip install django cryptography
```

## URL Structure

Main application routes (all under `/`):
- `/global_settings/` - Project and test configuration (login redirect)
- `/create_script/` - Script creation interface
- `/scripts/` - List all scripts
- `/login/` - User authentication (logout redirect)
- `/admin/` - Django admin interface

## Security Considerations

- **DEBUG Mode**: Currently set to `True` in settings.py - must be changed for production
- **Secret Key**: Using Django's default insecure key - must be replaced in production
- **Encryption**: Each project has its own Fernet encryption key stored in the database
- **CSRF Protection**: Enabled with HttpOnly cookies
- **Session Security**: HttpOnly session cookies configured

## Database Schema

- Uses SQLite by default (`db.sqlite3`)
- Custom dynamic tables created per project for script versioning
- Models use Django's default BigAutoField for primary keys