# Console Manager

## Overview
The Console Manager is a component of the ComAI Client Utilities that provides centralized console output formatting, error handling, and logging integration. It leverages the `rich` library to create beautiful and informative console output, making the CLI experience more user-friendly and consistent across the application.

## Features
- **Formatted Output**: Rich text formatting with colors, styles, and layout
- **Multiple Output Formats**: Support for text, JSON, and table formats
- **Error Handling**: Standardized error display with different severity levels
- **Progress Indicators**: Progress bars and spinners for long-running operations
- **Logging Integration**: Seamless integration with Python's logging module
- **Exception Formatting**: Formatted display of exceptions with traceback information

## Usage

### Basic Usage
```python
from src.utilities import get_console_manager

# Get the console manager instance
console = get_console_manager()

# Print a message
console.print("Hello, world!")

# Print a formatted message
console.print("[bold blue]ComAI Client[/bold blue]")

# Print different message types
console.print_info("This is an informational message.")
console.print_success("This is a success message.")
console.print_warning("This is a warning message.")
console.print_error("This is an error message.")
```

### JSON Output
```python
# Print JSON data
data = {
    "name": "ComAI Client",
    "version": "0.1.0",
    "components": ["CLI", "Blockchain Interface", "REST API", "MCP Server"]
}
console.print_json(data)

# Switch to JSON output format for all data
from src.utilities import OutputFormat
console.set_output_format(OutputFormat.JSON)
console.print(data)  # Will be printed as JSON
```

### Table Output
```python
# Print a table
headers = ["Component", "Status", "Priority"]
rows = [
    ["CLI", "In Progress", "High"],
    ["Blockchain Interface", "Completed", "High"],
    ["REST API", "Planned", "Medium"]
]
console.print_table(headers, rows, title="ComAI Client Components")
```

### Progress Indicators
```python
# Progress bar
with console.progress_bar(total=100, description="Processing") as progress:
    for i in range(10):
        # Do some work
        progress.update(10)

# Spinner
with console.spinner(text="Loading data"):
    # Do some work
    pass
```

### Exception Handling
```python
try:
    # Code that might raise an exception
    raise ValueError("This is a test exception")
except Exception as e:
    formatted = console.format_exception(e)
    console.print(formatted)
```

### Logging Integration
```python
# Set up logging
logger = console.setup_logging(level=logging.INFO)

# Use the logger
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
```

## Integration with Other Components

### CLI Integration
The Console Manager is particularly useful for CLI applications, providing a consistent and user-friendly interface for displaying information, errors, and progress.

```python
# In a CLI command
def list_command():
    console = get_console_manager()
    try:
        # Fetch data
        data = fetch_data()
        
        # Display as table
        headers = ["ID", "Name", "Status"]
        rows = [[item.id, item.name, item.status] for item in data]
        console.print_table(headers, rows, title="Items")
        
    except Exception as e:
        console.print_error(f"Failed to list items: {str(e)}")
        return 1
    
    return 0
```

### Blockchain Interface Integration
The Console Manager can be used to display blockchain operation status, transaction details, and connection information.

```python
# In a blockchain operation
def execute_transaction():
    console = get_console_manager()
    
    with console.spinner(text="Submitting transaction"):
        # Submit transaction
        result = submit_transaction()
    
    if result.success:
        console.print_success(f"Transaction submitted: {result.hash}")
    else:
        console.print_error(f"Transaction failed: {result.error}")
```

### Error Handling Integration
The Console Manager provides standardized error handling across the application, making it easier to display meaningful error messages to users.

```python
# In an error handler
def handle_error(error):
    console = get_console_manager()
    
    if isinstance(error, ConnectionError):
        console.print_error("Failed to connect to the blockchain node.")
    elif isinstance(error, TimeoutError):
        console.print_error("Operation timed out. Please try again later.")
    else:
        console.print_error(f"An unexpected error occurred: {str(error)}")
        
    # Log the full error details
    logger = logging.getLogger("com_ai")
    logger.error(f"Error details: {console.format_exception(error)}")
```

## Design Considerations

### Singleton Pattern
The Console Manager is implemented as a singleton to ensure consistent console output throughout the application. This means that all components share the same console instance, allowing for centralized configuration and state management.

### Rich Library Integration
The Console Manager leverages the `rich` library, which provides powerful text formatting, progress indicators, and logging integration. This allows for a more user-friendly and informative console experience.

### Output Format Flexibility
The Console Manager supports multiple output formats (text, JSON, table), allowing for flexible display of information based on the context and user preferences.

### Error Level Differentiation
Different error levels (info, warning, error) are displayed with distinct styles, making it easier for users to understand the severity of messages.

## Dependencies
- Python 3.12+
- rich 14.0.0+
