#!/usr/bin/env python3
"""
Comprehensive deployment script for Common supply chain platform.
Supports staging and production environments with health checks and rollback.
"""
import os
import sys
import subprocess
import time
import json
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import requests

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DeploymentError(Exception):
    """Custom exception for deployment errors."""
    pass


class DeploymentManager:
    """
    Comprehensive deployment manager.
    
    Features:
    - Environment-specific deployments
    - Database migrations
    - Health checks
    - Rollback capability
    - Zero-downtime deployments
    - Monitoring integration
    """
    
    def __init__(self, environment: str, config_file: str = None):
        self.environment = environment
        self.project_root = project_root
        self.config = self._load_config(config_file)
        self.deployment_id = f"deploy-{int(time.time())}"
        
        # Environment-specific settings
        self.env_config = self.config.get(environment, {})
        if not self.env_config:
            raise DeploymentError(f"No configuration found for environment: {environment}")
    
    def _load_config(self, config_file: str = None) -> Dict[str, Any]:
        """Load deployment configuration."""
        if config_file:
            config_path = Path(config_file)
        else:
            config_path = self.project_root / "deployment" / "config.json"
        
        if not config_path.exists():
            # Return default configuration
            return {
                "staging": {
                    "docker_registry": "localhost:5000",
                    "image_name": "common-api",
                    "replicas": 2,
                    "health_check_url": "http://localhost:8000/health",
                    "database_url": "postgresql://user:pass@localhost:5432/common_staging",
                    "redis_url": "redis://localhost:6379/1",
                    "environment_vars": {
                        "DEBUG": "False",
                        "LOG_LEVEL": "INFO"
                    }
                },
                "production": {
                    "docker_registry": "your-registry.com",
                    "image_name": "common-api",
                    "replicas": 4,
                    "health_check_url": "https://api.common.com/health",
                    "database_url": "postgresql://user:pass@prod-db:5432/common_prod",
                    "redis_url": "redis://prod-redis:6379/0",
                    "environment_vars": {
                        "DEBUG": "False",
                        "LOG_LEVEL": "WARNING"
                    }
                }
            }
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise DeploymentError(f"Failed to load config: {e}")
    
    def _run_command(self, command: List[str], cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command with error handling."""
        cwd = cwd or self.project_root
        
        print(f"Running: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check
            )
            
            if result.stdout:
                print(f"STDOUT: {result.stdout}")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            
            return result
            
        except subprocess.CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            raise DeploymentError(f"Command failed: {' '.join(command)}")
    
    def build_docker_image(self, tag: str = None) -> str:
        """Build Docker image."""
        print("🔨 Building Docker image...")
        
        if not tag:
            tag = f"{self.env_config['image_name']}:{self.deployment_id}"
        
        # Build image
        self._run_command([
            "docker", "build",
            "-t", tag,
            "--target", "production",
            "."
        ])
        
        # Tag for registry if specified
        registry = self.env_config.get('docker_registry')
        if registry:
            registry_tag = f"{registry}/{tag}"
            self._run_command(["docker", "tag", tag, registry_tag])
            tag = registry_tag
        
        print(f"✅ Docker image built: {tag}")
        return tag
    
    def push_docker_image(self, tag: str):
        """Push Docker image to registry."""
        registry = self.env_config.get('docker_registry')
        if not registry or registry == "localhost:5000":
            print("⏭️  Skipping image push (local registry)")
            return
        
        print(f"📤 Pushing Docker image: {tag}")
        self._run_command(["docker", "push", tag])
        print(f"✅ Image pushed: {tag}")
    
    def run_database_migrations(self):
        """Run database migrations."""
        print("🗃️  Running database migrations...")
        
        # Set environment variables
        env = os.environ.copy()
        env.update(self.env_config.get('environment_vars', {}))
        env['DATABASE_URL'] = self.env_config['database_url']
        
        try:
            # Run migrations using the migration manager
            result = subprocess.run([
                sys.executable, "-m", "app.core.migrations", "migrate"
            ], env=env, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise DeploymentError(f"Migration failed: {result.stderr}")
            
            print("✅ Database migrations completed")
            
        except Exception as e:
            raise DeploymentError(f"Migration error: {e}")
    
    def deploy_with_docker_compose(self, image_tag: str):
        """Deploy using Docker Compose."""
        print(f"🚀 Deploying with Docker Compose...")
        
        # Create environment-specific docker-compose file
        compose_file = self._create_docker_compose_file(image_tag)
        
        try:
            # Pull latest images
            self._run_command([
                "docker-compose", "-f", str(compose_file),
                "pull"
            ])
            
            # Deploy with rolling update
            self._run_command([
                "docker-compose", "-f", str(compose_file),
                "up", "-d", "--remove-orphans"
            ])
            
            print("✅ Docker Compose deployment completed")
            
        except Exception as e:
            raise DeploymentError(f"Docker Compose deployment failed: {e}")
    
    def _create_docker_compose_file(self, image_tag: str) -> Path:
        """Create environment-specific docker-compose file."""
        compose_content = {
            "version": "3.8",
            "services": {
                "api": {
                    "image": image_tag,
                    "ports": ["8000:8000"],
                    "environment": self.env_config.get('environment_vars', {}),
                    "depends_on": ["postgres", "redis"],
                    "restart": "unless-stopped",
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3,
                        "start_period": "40s"
                    }
                },
                "celery": {
                    "image": image_tag,
                    "environment": self.env_config.get('environment_vars', {}),
                    "depends_on": ["postgres", "redis"],
                    "restart": "unless-stopped",
                    "command": ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"]
                },
                "postgres": {
                    "image": "postgres:15",
                    "environment": {
                        "POSTGRES_DB": "common_db",
                        "POSTGRES_USER": "common_user",
                        "POSTGRES_PASSWORD": "common_password"
                    },
                    "volumes": ["postgres_data:/var/lib/postgresql/data"],
                    "restart": "unless-stopped"
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "volumes": ["redis_data:/data"],
                    "restart": "unless-stopped"
                }
            },
            "volumes": {
                "postgres_data": {},
                "redis_data": {}
            }
        }
        
        # Add replicas for production
        if self.environment == "production":
            compose_content["services"]["api"]["deploy"] = {
                "replicas": self.env_config.get('replicas', 2)
            }
        
        # Write compose file
        compose_file = self.project_root / f"docker-compose.{self.environment}.yml"
        with open(compose_file, 'w') as f:
            import yaml
            yaml.dump(compose_content, f, default_flow_style=False)
        
        return compose_file
    
    def wait_for_health_check(self, timeout: int = 300) -> bool:
        """Wait for application to become healthy."""
        print("🏥 Waiting for health check...")
        
        health_url = self.env_config.get('health_check_url', 'http://localhost:8000/health')
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=10)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get('status') == 'healthy':
                        print("✅ Application is healthy")
                        return True
                    else:
                        print(f"⚠️  Application status: {health_data.get('status', 'unknown')}")
                
            except requests.RequestException as e:
                print(f"⏳ Health check failed: {e}")
            
            time.sleep(10)
        
        print("❌ Health check timeout")
        return False
    
    def run_smoke_tests(self) -> bool:
        """Run smoke tests after deployment."""
        print("🧪 Running smoke tests...")
        
        base_url = self.env_config.get('health_check_url', 'http://localhost:8000').replace('/health', '')
        
        tests = [
            ("Health Check", f"{base_url}/health"),
            ("API Version", f"{base_url}/api/version"),
            ("Ready Check", f"{base_url}/health/ready")
        ]
        
        passed = 0
        for test_name, url in tests:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ {test_name}: PASS")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAIL (HTTP {response.status_code})")
            except Exception as e:
                print(f"❌ {test_name}: FAIL ({e})")
        
        success = passed == len(tests)
        print(f"🧪 Smoke tests: {passed}/{len(tests)} passed")
        return success
    
    def rollback_deployment(self, previous_tag: str = None):
        """Rollback to previous deployment."""
        print("🔄 Rolling back deployment...")
        
        if not previous_tag:
            # Try to find previous tag
            result = self._run_command([
                "docker", "images", "--format", "{{.Tag}}",
                self.env_config['image_name']
            ], check=False)
            
            if result.returncode == 0 and result.stdout:
                tags = result.stdout.strip().split('\n')
                # Find previous tag (excluding current)
                for tag in tags:
                    if tag != self.deployment_id:
                        previous_tag = f"{self.env_config['image_name']}:{tag}"
                        break
        
        if not previous_tag:
            raise DeploymentError("No previous deployment found for rollback")
        
        print(f"Rolling back to: {previous_tag}")
        
        # Deploy previous version
        self.deploy_with_docker_compose(previous_tag)
        
        # Wait for health check
        if self.wait_for_health_check():
            print("✅ Rollback completed successfully")
        else:
            raise DeploymentError("Rollback failed health check")
    
    def deploy(self, skip_tests: bool = False, dry_run: bool = False) -> bool:
        """Run complete deployment process."""
        print(f"🚀 Starting deployment to {self.environment}")
        print(f"📋 Deployment ID: {self.deployment_id}")
        
        if dry_run:
            print("🔍 DRY RUN MODE - No actual changes will be made")
            return True
        
        try:
            # Build and push image
            image_tag = self.build_docker_image()
            self.push_docker_image(image_tag)
            
            # Run database migrations
            self.run_database_migrations()
            
            # Deploy application
            self.deploy_with_docker_compose(image_tag)
            
            # Wait for health check
            if not self.wait_for_health_check():
                raise DeploymentError("Health check failed after deployment")
            
            # Run smoke tests
            if not skip_tests and not self.run_smoke_tests():
                raise DeploymentError("Smoke tests failed")
            
            print(f"✅ Deployment to {self.environment} completed successfully")
            print(f"🏷️  Image: {image_tag}")
            print(f"🆔 Deployment ID: {self.deployment_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            
            # Attempt rollback in production
            if self.environment == "production":
                try:
                    print("🔄 Attempting automatic rollback...")
                    self.rollback_deployment()
                except Exception as rollback_error:
                    print(f"❌ Rollback also failed: {rollback_error}")
            
            return False
    
    def cleanup_old_images(self, keep_count: int = 5):
        """Clean up old Docker images."""
        print(f"🧹 Cleaning up old images (keeping {keep_count})")
        
        try:
            # Get list of images
            result = self._run_command([
                "docker", "images", "--format", "{{.ID}} {{.Tag}}",
                self.env_config['image_name']
            ], check=False)
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > keep_count:
                    # Remove oldest images
                    for line in lines[keep_count:]:
                        image_id = line.split()[0]
                        self._run_command(["docker", "rmi", image_id], check=False)
            
            print("✅ Image cleanup completed")
            
        except Exception as e:
            print(f"⚠️  Image cleanup failed: {e}")


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy Common Supply Chain Platform")
    parser.add_argument("environment", choices=["staging", "production"], help="Deployment environment")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--skip-tests", action="store_true", help="Skip smoke tests")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run")
    parser.add_argument("--rollback", help="Rollback to specific tag")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old images")
    
    args = parser.parse_args()
    
    try:
        manager = DeploymentManager(args.environment, args.config)
        
        if args.rollback:
            manager.rollback_deployment(args.rollback)
        elif args.cleanup:
            manager.cleanup_old_images()
        else:
            success = manager.deploy(args.skip_tests, args.dry_run)
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
