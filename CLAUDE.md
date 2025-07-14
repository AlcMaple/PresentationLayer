# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based bridge health monitoring system (桥梁健康监控系统) for managing bridge inspection data. The system provides a comprehensive API for managing bridge components, diseases, assessment units, and quality metrics.

## Development Commands

### Starting the Application
```bash
# Development mode (with auto-reload)
python main.py

# Production mode
ENVIRONMENT=production python main.py
```

### Testing
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_database.py
```

### Database Management
- Database configuration is in `config/settings.py`
- Uses MySQL with SQLModel/SQLAlchemy
- Connection string format: `mysql+pymysql://user:password@host:port/database`

## Architecture

### Core Structure
- **FastAPI Application**: Main entry point in `main.py`
- **Modular Router System**: All API endpoints organized in `api/` directory with individual router modules
- **Generic CRUD Service**: Base service class in `services/base_crud.py` provides standardized CRUD operations
- **SQLModel Architecture**: Uses SQLModel for database models with automatic code generation
- **Middleware Stack**: Custom exception handling and CORS configuration

### Key Components

#### API Layer (`api/`)
- Each domain has its own router module (e.g., `bridge_types.py`, `bridge_diseases.py`)
- All routers are consolidated in `api/router.py`
- Follows RESTful conventions with standard CRUD endpoints

#### Models (`models/`)
- `base.py`: Base model with created_at/updated_at timestamps
- Domain-specific models inherit from BaseModel
- Uses SQLModel for both Pydantic schemas and SQLAlchemy models

#### Services (`services/`)
- `base_crud.py`: Generic CRUD service with pagination, filtering, and automatic code generation
- `code_generator.py`: Automatic code generation for entities
- `bridge_query.py`: Bridge-specific query services

#### Configuration (`config/`)
- `settings.py`: Pydantic Settings with environment-based configuration
- `database.py`: Database engine and session management

#### Exception Handling
- Custom exceptions in `exceptions/` directory
- Global exception middleware in `middleware/exception_handler.py`

### Data Flow Pattern
1. Request hits FastAPI router in `api/`
2. Router calls appropriate service method from `services/`
3. Service uses SQLModel to interact with database
4. Response formatted through Pydantic schemas in `schemas/`

### Code Generation
- Entities automatically get generated codes using the code generator service
- Codes follow a pattern specific to each table/entity type
- Duplicate checking is built into the CRUD operations

### Database Schema
The system manages bridge inspection data with these main entities:
- Categories (inspection categories)
- Assessment Units (评估单位)
- Bridge Types, Structures, Parts, Components
- Bridge Diseases and Quality metrics
- Bridge Scales and Quantities

### Testing Strategy
- Test configuration in `tests/conftest.py`
- Database session fixtures for testing
- Environment-specific test setup

## Development Notes

- Server runs on port 8002 by default (configurable via settings)
- Development mode enables CORS for all origins
- All models include soft delete functionality via `is_active` field
- Pagination is standardized through `PageParams` class
- Filtering capabilities built into base CRUD service