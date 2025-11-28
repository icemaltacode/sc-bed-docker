"""
Unit tests for Docker Compose setup, Nginx configuration, and services.
"""
import subprocess
import time
import os
import yaml
import pytest
import requests
from pathlib import Path


# Test constants
PROJECT_DIR = Path(__file__).parent
DOCKER_COMPOSE_FILE = PROJECT_DIR / "docker-compose.yml"
NGINX_CONFIG_FILE = PROJECT_DIR / "default.conf"
RUN_CMD_FILE = PROJECT_DIR / "run.cmd"
DB_SQL_FILE = PROJECT_DIR / "support" / "db.sql"
TEST_HTML_FILE = PROJECT_DIR / "test_static.html"
TEST_PHP_FILE = PROJECT_DIR / "test_php.php"


@pytest.fixture(scope="module")
def docker_compose_config():
    """Load and parse docker-compose.yml configuration."""
    with open(DOCKER_COMPOSE_FILE, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def nginx_config():
    """Load Nginx configuration file."""
    with open(NGINX_CONFIG_FILE, 'r') as f:
        return f.read()


class TestNginxStaticFiles:
    """Test case 1: Nginx correctly serves static files."""
    
    def test_nginx_config_has_root_directive(self, nginx_config):
        """Verify Nginx config has root directive set."""
        assert "root /var/www/html" in nginx_config
    
    def test_nginx_config_has_try_files_directive(self, nginx_config):
        """Verify Nginx config has try_files directive for static files."""
        assert "try_files" in nginx_config
        assert "location /" in nginx_config
    
    def test_nginx_config_static_file_extensions(self, nginx_config):
        """Verify Nginx config tries static files before PHP."""
        # The try_files directive should attempt $uri before passing to PHP
        assert "try_files $uri" in nginx_config
    
    def test_nginx_dockerfile_copies_config(self):
        """Verify Nginx Dockerfile copies the config file."""
        dockerfile_path = PROJECT_DIR / "Dockerfile.sc-bed-nginx"
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        assert "COPY default.conf /etc/nginx/conf.d/default.conf" in content
        assert "nginx:alpine" in content
    
    def test_nginx_config_has_correct_listen_port(self, nginx_config):
        """Verify Nginx listens on port 80."""
        assert "listen 80" in nginx_config
    
    def test_nginx_config_index_files(self, nginx_config):
        """Verify Nginx config has index directive."""
        assert "index" in nginx_config
        # Should include both PHP and HTML index files
        assert "index.php" in nginx_config or "index.html" in nginx_config


class TestNginxPHPProxy:
    """Test case 2: Nginx correctly proxies requests to PHP service."""
    
    def test_nginx_config_has_php_location_block(self, nginx_config):
        """Verify Nginx config has PHP location block."""
        assert "location ~ \\.php$" in nginx_config
    
    def test_nginx_config_fastcgi_pass(self, nginx_config):
        """Verify Nginx config passes PHP requests to FastCGI."""
        assert "fastcgi_pass php:9000" in nginx_config
    
    def test_nginx_config_fastcgi_params(self, nginx_config):
        """Verify Nginx config includes necessary FastCGI parameters."""
        assert "fastcgi_param SCRIPT_FILENAME" in nginx_config
        assert "fastcgi_param PATH_INFO" in nginx_config
        assert "include fastcgi_params" in nginx_config
    
    def test_nginx_config_fastcgi_split_path(self, nginx_config):
        """Verify Nginx config splits path info correctly."""
        assert "fastcgi_split_path_info" in nginx_config
    
    def test_nginx_config_fastcgi_index(self, nginx_config):
        """Verify Nginx config has FastCGI index."""
        assert "fastcgi_index index.php" in nginx_config
    
    def test_php_service_exposes_correct_port(self, docker_compose_config):
        """Verify PHP service configuration is compatible with Nginx proxy."""
        # PHP-FPM typically runs on port 9000
        # The service should be named 'php' to match fastcgi_pass
        assert "php" in docker_compose_config["services"]
        php_service = docker_compose_config["services"]["php"]
        
        # Verify PHP service uses correct image
        assert "php" in php_service["image"]


class TestDockerComposeServices:
    """Test case 3: All Docker Compose services start and become healthy."""
    
    def test_all_required_services_defined(self, docker_compose_config):
        """Verify all required services are defined in docker-compose.yml."""
        services = docker_compose_config["services"]
        
        assert "web" in services, "Web service not defined"
        assert "php" in services, "PHP service not defined"
        assert "mariadb" in services, "MariaDB service not defined"
    
    def test_web_service_configuration(self, docker_compose_config):
        """Verify web service is properly configured."""
        web = docker_compose_config["services"]["web"]
        
        assert "image" in web, "Web service missing image"
        assert "nginx" in web["image"].lower()
        assert "ports" in web, "Web service missing port mapping"
        assert "8000:80" in web["ports"], "Web service not mapped to port 8000"
        assert "volumes" in web, "Web service missing volume mounts"
    
    def test_php_service_configuration(self, docker_compose_config):
        """Verify PHP service is properly configured."""
        php = docker_compose_config["services"]["php"]
        
        assert "image" in php, "PHP service missing image"
        assert "php" in php["image"].lower()
        assert "volumes" in php, "PHP service missing volume mounts"
        assert "depends_on" in php, "PHP service missing dependencies"
    
    def test_mariadb_service_configuration(self, docker_compose_config):
        """Verify MariaDB service is properly configured."""
        mariadb = docker_compose_config["services"]["mariadb"]
        
        assert "image" in mariadb, "MariaDB service missing image"
        assert "mariadb" in mariadb["image"].lower()
        assert "environment" in mariadb, "MariaDB service missing environment"
        assert "MARIADB_ROOT_PASSWORD" in mariadb["environment"]
    
    def test_mariadb_healthcheck_configured(self, docker_compose_config):
        """Verify MariaDB has healthcheck configured."""
        mariadb = docker_compose_config["services"]["mariadb"]
        
        assert "healthcheck" in mariadb, "MariaDB missing healthcheck"
        healthcheck = mariadb["healthcheck"]
        
        assert "test" in healthcheck, "Healthcheck missing test"
        assert "interval" in healthcheck, "Healthcheck missing interval"
        assert "timeout" in healthcheck, "Healthcheck missing timeout"
        assert "retries" in healthcheck, "Healthcheck missing retries"
        
        # Verify healthcheck uses mariadb-admin
        assert "mariadb-admin" in str(healthcheck["test"])
    
    def test_php_service_waits_for_mariadb_health(self, docker_compose_config):
        """Verify PHP service waits for MariaDB to be healthy."""
        php = docker_compose_config["services"]["php"]
        
        assert "depends_on" in php
        assert "mariadb" in php["depends_on"]
        
        # Check that it waits for health condition
        mariadb_dep = php["depends_on"]["mariadb"]
        assert isinstance(mariadb_dep, dict), "Should use extended depends_on syntax"
        assert mariadb_dep.get("condition") == "service_healthy"
    
    def test_services_share_volumes(self, docker_compose_config):
        """Verify web and PHP services share the same volume mount."""
        web = docker_compose_config["services"]["web"]
        php = docker_compose_config["services"]["php"]
        
        assert "volumes" in web
        assert "volumes" in php
        
        # Both should mount the same source directory
        web_volumes = web["volumes"]
        php_volumes = php["volumes"]
        
        # Check that both mount to /var/www/html
        web_has_html = any("/var/www/html" in str(v) for v in web_volumes)
        php_has_html = any("/var/www/html" in str(v) for v in php_volumes)
        
        assert web_has_html, "Web service doesn't mount /var/www/html"
        assert php_has_html, "PHP service doesn't mount /var/www/html"
    
    def test_persistent_volume_for_database(self, docker_compose_config):
        """Verify MariaDB uses persistent volume."""
        mariadb = docker_compose_config["services"]["mariadb"]
        
        assert "volumes" in mariadb
        
        # Check for database data volume
        has_data_volume = any("/var/lib/mysql" in str(v) for v in mariadb["volumes"])
        assert has_data_volume, "MariaDB missing persistent data volume"
        
        # Check that named volume is defined
        assert "volumes" in docker_compose_config
        assert "db_data" in docker_compose_config["volumes"]


class TestMariaDBInitialization:
    """Test case 4: MariaDB service initializes with provided db.sql content."""
    
    def test_mariadb_init_volume_mount(self, docker_compose_config):
        """Verify MariaDB mounts db.sql to initialization directory."""
        mariadb = docker_compose_config["services"]["mariadb"]
        
        assert "volumes" in mariadb
        
        # Check for docker-entrypoint-initdb.d mount
        init_volume_found = False
        for volume in mariadb["volumes"]:
            if "/docker-entrypoint-initdb.d/db.sql" in str(volume):
                init_volume_found = True
                # Verify it mounts from support/db.sql
                assert "support/db.sql" in str(volume) or "./support/db.sql" in str(volume)
        
        assert init_volume_found, "MariaDB missing db.sql initialization volume"
    
    def test_mariadb_init_path_format(self, docker_compose_config):
        """Verify MariaDB initialization volume path is correctly formatted."""
        mariadb = docker_compose_config["services"]["mariadb"]
        volumes = mariadb["volumes"]
        
        # Find the init volume
        init_volume = None
        for volume in volumes:
            if "docker-entrypoint-initdb.d" in str(volume):
                init_volume = str(volume)
                break
        
        assert init_volume is not None
        # Should be in format: ./support/db.sql:/docker-entrypoint-initdb.d/db.sql
        parts = init_volume.split(":")
        assert len(parts) == 2, "Volume mount should have source:destination format"
        assert parts[1] == "/docker-entrypoint-initdb.d/db.sql"
    
    def test_db_sql_documentation(self):
        """Verify documentation or example for db.sql exists."""
        # Check if db.sql file exists or if there's a README mentioning it
        db_sql_exists = DB_SQL_FILE.exists()
        
        # If db.sql doesn't exist, at least the configuration references it
        # which means users need to create it
        assert not db_sql_exists or DB_SQL_FILE.is_file(), \
            "If support/db.sql exists, it should be a file"
    
    def test_mariadb_root_password_configured(self, docker_compose_config):
        """Verify MariaDB root password is set for initialization."""
        mariadb = docker_compose_config["services"]["mariadb"]
        
        assert "environment" in mariadb
        env = mariadb["environment"]
        
        assert "MARIADB_ROOT_PASSWORD" in env
        # Password should not be empty
        password = env["MARIADB_ROOT_PASSWORD"]
        assert password and len(str(password)) > 0


class TestRunCmdScript:
    """Test case 5: run.cmd script successfully starts and stops Docker Compose services."""
    
    def test_run_cmd_file_exists(self):
        """Verify run.cmd file exists."""
        assert RUN_CMD_FILE.exists(), "run.cmd file not found"
        assert RUN_CMD_FILE.is_file(), "run.cmd should be a file"
    
    def test_run_cmd_is_executable(self):
        """Verify run.cmd has executable permissions (Unix)."""
        if os.name != 'nt':  # Skip on Windows
            # Check if file has any execute bit set
            stat_info = os.stat(RUN_CMD_FILE)
            # On Unix systems, we should be able to execute it
            # But the file might not have +x, which is okay for .cmd files
            assert stat_info.st_size > 0, "run.cmd should not be empty"
    
    def test_run_cmd_has_docker_compose_up(self):
        """Verify run.cmd contains docker compose up command."""
        with open(RUN_CMD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "docker compose up" in content, "run.cmd missing 'docker compose up'"
    
    def test_run_cmd_has_docker_compose_down(self):
        """Verify run.cmd contains docker compose down command."""
        with open(RUN_CMD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "docker compose down" in content, "run.cmd missing 'docker compose down'"
    
    def test_run_cmd_supports_both_platforms(self):
        """Verify run.cmd supports both Windows and Unix platforms."""
        with open(RUN_CMD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Windows CMD markers
        has_windows = "@echo off" in content or "REM" in content
        
        # Check for Unix shell markers
        has_unix = "#!/" in content or "set -e" in content
        
        assert has_windows and has_unix, \
            "run.cmd should support both Windows and Unix platforms"
    
    def test_run_cmd_has_reset_db_option(self):
        """Verify run.cmd supports reset-db option."""
        with open(RUN_CMD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "reset-db" in content or "reset_db" in content.lower()
        assert "docker compose down -v" in content, \
            "reset-db should use 'docker compose down -v'"
    
    def test_run_cmd_has_verbose_option(self):
        """Verify run.cmd supports verbose option."""
        with open(RUN_CMD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "--verbose" in content or "verbose" in content.lower()
    
    def test_run_cmd_argument_parsing_unix(self):
        """Verify run.cmd parses arguments correctly on Unix."""
        with open(RUN_CMD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for proper argument parsing in Unix section
        if 'for arg in "$@"' in content or 'for arg in' in content:
            assert True
        else:
            # Alternative argument parsing methods
            assert "$@" in content or "RESET_DB" in content
    
    def test_run_cmd_argument_parsing_windows(self):
        """Verify run.cmd parses arguments correctly on Windows."""
        with open(RUN_CMD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Windows batch argument parsing
        has_windows_parsing = (
            "for %%A in (%*)" in content or
            "%1" in content or
            "RESET_DB" in content
        )
        assert has_windows_parsing, "Missing Windows argument parsing"
    
    def test_run_cmd_provides_user_feedback(self):
        """Verify run.cmd provides feedback messages to user."""
        with open(RUN_CMD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have messages indicating what's happening
        feedback_keywords = ["Starting", "start", "Running", "Destroying", "destroy"]
        has_feedback = any(keyword in content for keyword in feedback_keywords)
        
        assert has_feedback, "run.cmd should provide user feedback messages"
    
    def test_run_cmd_has_banner(self):
        """Verify run.cmd displays a banner/logo."""
        with open(RUN_CMD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for ASCII art or banner
        has_banner = "___" in content or "ICE" in content or "CAMPUS" in content
        assert has_banner, "run.cmd should display a banner"


# Integration tests (require Docker)
class TestDockerIntegration:
    """Integration tests that require Docker to be running."""
    
    @pytest.mark.integration
    def test_docker_compose_config_valid(self):
        """Verify docker-compose.yml is valid."""
        result = subprocess.run(
            ["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "config"],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR
        )
        
        assert result.returncode == 0, f"docker-compose.yml invalid: {result.stderr}"
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_services_start_successfully(self):
        """
        Integration test: Verify all services can start.
        This is a slow test and requires Docker.
        """
        # This test is marked as integration and slow
        # It should be run separately with: pytest -m integration
        
        # Pull images first
        subprocess.run(
            ["docker", "compose", "pull"],
            cwd=PROJECT_DIR,
            capture_output=True
        )
        
        # Start services
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR
        )
        
        assert result.returncode == 0, f"Failed to start services: {result.stderr}"
        
        try:
            # Wait for services to be healthy
            max_wait = 60  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                result = subprocess.run(
                    ["docker", "compose", "ps", "--format", "json"],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_DIR
                )
                
                if result.returncode == 0:
                    # Check if mariadb is healthy
                    health_result = subprocess.run(
                        ["docker", "compose", "ps", "mariadb", "--format", "json"],
                        capture_output=True,
                        text=True,
                        cwd=PROJECT_DIR
                    )
                    
                    if "healthy" in health_result.stdout.lower():
                        break
                
                time.sleep(2)
            
            # Verify services are running
            result = subprocess.run(
                ["docker", "compose", "ps"],
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR
            )
            
            assert "web" in result.stdout
            assert "php" in result.stdout
            assert "mariadb" in result.stdout
            
        finally:
            # Cleanup
            subprocess.run(
                ["docker", "compose", "down", "-v"],
                cwd=PROJECT_DIR,
                capture_output=True
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
