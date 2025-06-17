# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

This is a Django + PostgreSQL project using Docker Compose and Just as the task runner.

### Working Directory
Navigate to `packages/django-app/` for most development tasks.

### Development Setup
- `just init` - Initialize project (create volumes, build, setup database)
- `just copy-env` - Copy environment template file
- `just generate-secret-key` - Generate Django secret key for .env
- `just create-superuser` - Create Django admin user

### Django Commands
- `just django-admin <command>` - Run Django management commands with safety checks
- `just migrate` - Run database migrations
- `just makemigrations` - Create new migrations
- `just shell` - Django shell
- `just runserver` - Start development server

### Testing
- `just test` - Run tests (excludes integration tests marked with `@pytest.mark.integration`)
- Tests use pytest with `--reuse-db` and coverage reporting
- Test files: `tests.py`, `test_*.py`, `*_test.py`, `*_tests.py`

### Database Management
- `just reload-db [DATA]` - Reload database with fixture (defaults to dev_data.json)
- `just dump-data` - Export database data to stdout
- `just create-json-backup [location]` - Create JSON backup
- `just create-pgdump [location]` - Create PostgreSQL dump backup

### Docker Management
- `just up` - Start services
- `just up-d` - Start services in background
- `just down` - Stop services
- `just build` - Build Docker images
- `just logs [service]` - View logs

## Architecture

### Project Structure
- **Monorepo**: Single project with packages in `packages/`
- **Django App**: Main application in `packages/django-app/app/`
- **Custom User Model**: Uses `core.User` as AUTH_USER_MODEL
- **Docker Compose**: PostgreSQL database + Django web service

### Code Organization
- `app/` - Main Django project
- `core/` - Core models (User), admin, fixtures
- `common/` - Shared utilities and base classes
  - `models/` - Model mixins (UUID, timestamps, soft delete)
  - `repositories/` - Repository pattern base classes
  - `managers/` - Custom model managers
  - `forms/` - Form base classes and mixins

### Key Patterns
- **Repository Pattern**: Use `BaseRepository` for data access
- **Model Mixins**: UUID, timestamps, soft delete functionality
- **Soft Delete**: Models can inherit `SoftDeleteTimestampMixin` for logical deletion
- **Custom Managers**: Extend Django's model managers for complex queries

### Environment Configuration
- Uses environment variables for sensitive data (SECRET_KEY, DEBUG, etc.)
- Database safety checks prevent accidental production commands
- Separate test settings in `app.test_settings`
