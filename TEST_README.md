# Testing Documentation

This document describes the unit tests for the sc-bed-docker project.

## Test Coverage

The test suite covers the following areas:

### 1. Nginx Static File Serving
Tests that verify the Nginx configuration correctly serves static files:
- Root directive configuration
- Try_files directive for static content
- Static files are attempted before PHP processing
- Correct port configuration (80)
- Index file configuration
- Dockerfile properly copies configuration

### 2. Nginx PHP Proxy Configuration
Tests that verify Nginx correctly proxies PHP requests to the PHP-FPM service:
- PHP location block configuration
- FastCGI pass to PHP service on port 9000
- Required FastCGI parameters (SCRIPT_FILENAME, PATH_INFO)
- FastCGI split path info
- FastCGI index configuration
- PHP service compatibility

### 3. Docker Compose Services
Tests that verify all services are properly configured:
- All required services (web, php, mariadb) are defined
- Web service configuration (image, ports, volumes)
- PHP service configuration (image, volumes, dependencies)
- MariaDB service configuration (image, environment, ports)
- MariaDB healthcheck configuration
- PHP service waits for MariaDB to be healthy
- Services share appropriate volumes
- Persistent database volume configuration

### 4. MariaDB Initialization
Tests that verify MariaDB initializes with db.sql:
- db.sql volume mount to docker-entrypoint-initdb.d
- Correct volume path format
- Root password configuration for initialization
- Documentation for db.sql

### 5. run.cmd Script
Tests that verify the run.cmd script functionality:
- Script file exists
- Contains docker compose up command
- Contains docker compose down command
- Supports both Windows and Unix platforms
- Reset database option (--reset-db)
- Verbose option (--verbose)
- Proper argument parsing for both platforms
- User feedback messages
- Banner/logo display

### 6. Integration Tests
Optional integration tests that require Docker:
- Validates docker-compose.yml configuration
- Tests that services start successfully
- Verifies services become healthy

## Setup

### Install Dependencies

```bash
pip install -r requirements-test.txt
```

Or with a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-test.txt
```

## Running Tests

### Run All Unit Tests (Fast)

Run unit tests that don't require Docker:

```bash
pytest -m "not integration and not slow"
```

### Run All Tests Including Integration Tests

Run all tests including those that require Docker:

```bash
pytest
```

### Run Only Integration Tests

Run only the integration tests:

```bash
pytest -m integration
```

### Run with Coverage Report

```bash
pytest --cov=. --cov-report=html
```

This generates a coverage report in `htmlcov/index.html`.

### Run Specific Test Classes

```bash
# Test Nginx static file configuration
pytest test_docker_setup.py::TestNginxStaticFiles -v

# Test Nginx PHP proxy configuration
pytest test_docker_setup.py::TestNginxPHPProxy -v

# Test Docker Compose services
pytest test_docker_setup.py::TestDockerComposeServices -v

# Test MariaDB initialization
pytest test_docker_setup.py::TestMariaDBInitialization -v

# Test run.cmd script
pytest test_docker_setup.py::TestRunCmdScript -v
```

### Run Specific Test Methods

```bash
pytest test_docker_setup.py::TestNginxStaticFiles::test_nginx_config_has_root_directive -v
```

## Test Output

### Successful Run Example

```
test_docker_setup.py::TestNginxStaticFiles::test_nginx_config_has_root_directive PASSED
test_docker_setup.py::TestNginxStaticFiles::test_nginx_config_has_try_files_directive PASSED
test_docker_setup.py::TestNginxPHPProxy::test_nginx_config_fastcgi_pass PASSED
test_docker_setup.py::TestDockerComposeServices::test_all_required_services_defined PASSED
...
============================== 35 passed in 0.45s ===============================
```

### Failed Test Example

If a test fails, pytest will show detailed information:

```
FAILED test_docker_setup.py::TestNginxStaticFiles::test_nginx_config_has_root_directive
AssertionError: assert 'root /var/www/html' in <nginx_config>
```

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run unit tests
        run: pytest -m "not integration and not slow"
      - name: Run integration tests
        run: pytest -m integration
```

## Test Structure

The test file (`test_docker_setup.py`) is organized into classes:

- `TestNginxStaticFiles` - Nginx static file serving tests
- `TestNginxPHPProxy` - Nginx PHP proxy tests
- `TestDockerComposeServices` - Docker Compose service configuration tests
- `TestMariaDBInitialization` - MariaDB initialization tests
- `TestRunCmdScript` - run.cmd script tests
- `TestDockerIntegration` - Integration tests (requires Docker)

## Adding New Tests

To add new tests:

1. Create a new test method in the appropriate class
2. Follow the naming convention: `test_<description>`
3. Use descriptive docstrings
4. Use appropriate assertions with clear error messages

Example:

```python
def test_my_new_feature(self, docker_compose_config):
    """Verify my new feature works correctly."""
    # Arrange
    service = docker_compose_config["services"]["web"]
    
    # Act & Assert
    assert "my_feature" in service, "Feature not configured"
```

## Troubleshooting

### Import Errors

If you get import errors for `yaml` or `pytest`:

```bash
pip install -r requirements-test.txt
```

### Integration Tests Failing

Integration tests require Docker to be running:

```bash
docker --version  # Verify Docker is installed
docker compose version  # Verify Docker Compose is available
```

### Permission Issues on Unix

If you get permission errors running the tests:

```bash
chmod +x run.cmd
```

## Notes

- Unit tests (non-integration) are fast and don't require Docker
- Integration tests require Docker and may take longer to run
- The test suite validates configuration files, not runtime behavior (except integration tests)
- For full end-to-end testing, run the integration tests with Docker running
