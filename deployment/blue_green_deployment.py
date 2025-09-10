#!/usr/bin/env python3
"""
Blue-green deployment orchestration script.

This script provides:
1. Zero-downtime blue-green deployments
2. Automated health validation
3. Traffic switching coordination
4. Automatic rollback on failure
5. Environment parity validation
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.core.deployment_management import (
    BlueGreenDeploymentManager,
    EnvironmentParityValidator,
    DeploymentConfig,
    DeploymentStrategy,
    EnvironmentType
)
from app.core.logging import get_logger

logger = get_logger(__name__)


async def main():
    """Main deployment orchestration function."""
    parser = argparse.ArgumentParser(description="Blue-Green Deployment Manager")
    parser.add_argument("--environment", 
                       choices=["staging", "production"], 
                       required=True,
                       help="Target environment")
    parser.add_argument("--image-tag", 
                       required=True,
                       help="Docker image tag to deploy")
    parser.add_argument("--validate-parity", 
                       action="store_true",
                       help="Validate environment parity before deployment")
    parser.add_argument("--dry-run", 
                       action="store_true",
                       help="Perform dry run without actual deployment")
    parser.add_argument("--skip-health-check", 
                       action="store_true",
                       help="Skip health check validation")
    parser.add_argument("--rollback-on-failure", 
                       action="store_true", 
                       default=True,
                       help="Automatically rollback on deployment failure")
    
    args = parser.parse_args()
    
    try:
        # Create deployment configuration
        config = DeploymentConfig(
            environment=EnvironmentType(args.environment),
            strategy=DeploymentStrategy.BLUE_GREEN,
            image_tag=args.image_tag,
            replicas=4 if args.environment == "production" else 2,
            health_check_url=f"https://api{'.' if args.environment == 'production' else '-staging.'}common.com/health",
            health_check_timeout=300,
            rollback_on_failure=args.rollback_on_failure
        )
        
        print(f"🚀 Starting blue-green deployment to {args.environment}")
        print(f"📦 Image: {args.image_tag}")
        print(f"🔧 Configuration: {config.strategy.value}")
        
        if args.dry_run:
            print("🔍 DRY RUN MODE - No actual changes will be made")
            return 0
        
        # Validate environment parity if requested
        if args.validate_parity:
            print("🔍 Validating environment parity...")
            validator = EnvironmentParityValidator()
            
            source_env = EnvironmentType.STAGING if args.environment == "production" else EnvironmentType.DEVELOPMENT
            target_env = EnvironmentType(args.environment)
            
            parity_results = await validator.validate_environment_parity(source_env, target_env)
            
            if parity_results["overall_status"] != "passed":
                print("❌ Environment parity validation failed:")
                for check_name, result in parity_results["checks"].items():
                    if not result["passed"]:
                        print(f"  - {check_name}: {result.get('message', 'Failed')}")
                
                if args.environment == "production":
                    print("🛑 Stopping deployment due to parity issues in production")
                    return 1
                else:
                    print("⚠️  Continuing with deployment despite parity issues (staging)")
            else:
                print("✅ Environment parity validation passed")
        
        # Create deployment manager
        deployment_manager = BlueGreenDeploymentManager(config)
        
        # Execute deployment
        success = await deployment_manager.deploy()
        
        if success:
            print("✅ Blue-green deployment completed successfully!")
            print(f"🆔 Deployment ID: {deployment_manager.deployment_id}")
            print(f"⏱️  Duration: {deployment_manager.metrics.duration_seconds:.2f} seconds")
            return 0
        else:
            print("❌ Blue-green deployment failed!")
            print(f"🆔 Deployment ID: {deployment_manager.deployment_id}")
            print(f"❌ Error: {deployment_manager.metrics.error_message}")
            
            if deployment_manager.metrics.rollback_performed:
                print("🔄 Automatic rollback was performed")
            
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Deployment interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Deployment failed with error: {e}")
        logger.error("Deployment script failed", error=str(e))
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
