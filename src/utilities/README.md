# ComAI Client Utilities

This package provides essential infrastructure services for the ComAI Client, focusing on centralizing cross-cutting concerns like path management and environment configuration.

## Overview

The Utilities component provides a foundation for other components to build upon, ensuring consistency across the codebase, reducing duplication, and simplifying maintenance by providing a single source of truth for paths and environment variables.

## Components

### Path Manager

The Path Manager centralizes path handling and management throughout the application to avoid hardcoded paths and ensure consistency.

#### Features

- Single source of truth for all application paths
- Path resolution for different environments (development, testing, production)
- Support for both absolute and relative path resolution
- Platform-specific path differences handling
- Path validation and normalization
- Path registration from different components
- Path substitution with environment variables
- Path discovery for configuration files, data directories, etc.
- Path caching for improved performance

#### Usage

```python
from src.utilities import get_path_manager

# Get the singleton instance
path_manager = get_path_manager()

# Register a path
path_manager.register_path("my_config", "${project_root}/config/my_config.json")

# Resolve a path
config_path = path_manager.resolve_path("my_config")

# Resolve a directory and create it if it doesn't exist
data_dir = path_manager.resolve_directory("data_dir", create=True)

# Join paths
log_file = path_manager.join_path("logs_dir", "app.log")

# Find a file in multiple search paths
config_file = path_manager.find_file("config.json", ["config_dir", "project_root"])
```

### Environment Manager

The Environment Manager centralizes environment configuration and management to ensure consistent access to environment variables and configuration settings.

#### Features

- Single source of truth for all environment variables
- Environment-specific configuration (development, testing, production)
- Loading configuration from different sources (env files, system env vars)
- Default values for missing environment variables
- Type conversion for environment variables
- Validation of environment variables
- Secure handling of sensitive information
- Dynamic environment variable updates
- Environment variable registration from different components

#### Usage

```python
from src.utilities import get_environment_manager

# Get the singleton instance
env_manager = get_environment_manager()

# Register a variable with metadata
env_manager.register_var(
    "API_KEY",
    description="API key for external service",
    required=True,
    pattern=r"^[A-Za-z0-9]{32}$"
)

# Get a variable
api_key = env_manager.get_var("API_KEY")

# Get a variable with a default value
log_level = env_manager.get_var("LOG_LEVEL", default="INFO")

# Get a variable as a specific type
port = env_manager.get_var_as_int("PORT", default=8080)
debug = env_manager.get_var_as_bool("DEBUG", default=False)
hosts = env_manager.get_var_as_list("ALLOWED_HOSTS", default=["localhost"])
config = env_manager.get_var_as_dict("CONFIG", default={"timeout": 30})

# Check the environment type
if env_manager.is_development():
    # Development-specific code
    pass
elif env_manager.is_production():
    # Production-specific code
    pass
```

## Installation

The utilities component has the following dependencies:

- Python 3.12
- python-dotenv
- pydantic

Install the dependencies using pip:

```bash
pip install -r requirements.txt
```

## Testing

Run the tests for the utilities component:

```bash
python -m unittest discover -s tests/utilities
```
