#!/bin/bash

# Comprehensive deployment script for Common Supply Chain Platform
# Supports staging and production environments with health checks and rollback

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ID="deploy-$(date +%s)"
LOG_FILE="/tmp/common-deploy-${DEPLOYMENT_ID}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] ENVIRONMENT

Deploy Common Supply Chain Platform to specified environment.

ARGUMENTS:
    ENVIRONMENT     Target environment (staging|production)

OPTIONS:
    -h, --help      Show this help message
    -t, --tag       Docker image tag (default: latest)
    -s, --skip-tests Skip smoke tests
    -d, --dry-run   Perform dry run without actual deployment
    -r, --rollback  Rollback to previous version
    -c, --cleanup   Clean up old images and containers
    -v, --verbose   Enable verbose logging

EXAMPLES:
    $0 staging
    $0 production --tag v1.2.3
    $0 staging --dry-run
    $0 production --rollback

EOF
}

# Parse command line arguments
ENVIRONMENT=""
IMAGE_TAG="latest"
SKIP_TESTS=false
DRY_RUN=false
ROLLBACK=false
CLEANUP=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -r|--rollback)
            ROLLBACK=true
            shift
            ;;
        -c|--cleanup)
            CLEANUP=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        staging|production)
            ENVIRONMENT="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "Environment is required"
    usage
    exit 1
fi

if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    log_error "Environment must be 'staging' or 'production'"
    exit 1
fi

# Set verbose mode
if [[ "$VERBOSE" == "true" ]]; then
    set -x
fi

# Load environment configuration
ENV_FILE="$PROJECT_ROOT/.env.$ENVIRONMENT"
if [[ -f "$ENV_FILE" ]]; then
    log "Loading environment configuration from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
else
    log_warning "Environment file $ENV_FILE not found"
fi

# Configuration based on environment
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.$ENVIRONMENT.yml"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-http://localhost:8000/health}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"
DEPLOYMENT_TIMEOUT="${DEPLOYMENT_TIMEOUT:-600}"

# Functions
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("docker" "docker-compose" "curl" "jq")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check compose file
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

build_image() {
    log "Building Docker image..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would build image with tag $IMAGE_TAG"
        return 0
    fi
    
    # Build image
    docker build \
        --target production \
        --tag "common-api:$IMAGE_TAG" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse HEAD)" \
        --build-arg VERSION="$IMAGE_TAG" \
        "$PROJECT_ROOT"
    
    # Tag for registry if specified
    if [[ -n "${DOCKER_REGISTRY:-}" ]]; then
        docker tag "common-api:$IMAGE_TAG" "$DOCKER_REGISTRY/common-api:$IMAGE_TAG"
    fi
    
    log_success "Image built successfully"
}

push_image() {
    if [[ -z "${DOCKER_REGISTRY:-}" ]]; then
        log "No registry specified, skipping image push"
        return 0
    fi
    
    log "Pushing image to registry..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would push image $DOCKER_REGISTRY/common-api:$IMAGE_TAG"
        return 0
    fi
    
    docker push "$DOCKER_REGISTRY/common-api:$IMAGE_TAG"
    log_success "Image pushed successfully"
}

run_migrations() {
    log "Running database migrations..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would run database migrations"
        return 0
    fi
    
    # Run migrations using Python script
    cd "$PROJECT_ROOT"
    python -m app.core.migrations migrate
    
    log_success "Database migrations completed"
}

deploy_services() {
    log "Deploying services..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would deploy services using $COMPOSE_FILE"
        return 0
    fi
    
    # Set image tag for compose
    export IMAGE_TAG="$IMAGE_TAG"
    
    # Deploy with docker-compose
    docker-compose -f "$COMPOSE_FILE" pull
    docker-compose -f "$COMPOSE_FILE" up -d --remove-orphans
    
    log_success "Services deployed"
}

wait_for_health() {
    log "Waiting for health check..."
    
    local start_time=$(date +%s)
    local timeout="$HEALTH_CHECK_TIMEOUT"
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [[ $elapsed -gt $timeout ]]; then
            log_error "Health check timeout after ${timeout}s"
            return 1
        fi
        
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log_success "Health check passed"
            return 0
        fi
        
        log "Health check failed, retrying in 10s... (${elapsed}s elapsed)"
        sleep 10
    done
}

run_smoke_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        log "Skipping smoke tests"
        return 0
    fi
    
    log "Running smoke tests..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would run smoke tests"
        return 0
    fi
    
    # Basic API tests
    local base_url="${HEALTH_CHECK_URL%/health}"
    local tests=(
        "$base_url/health"
        "$base_url/health/ready"
        "$base_url/api/version"
    )
    
    local passed=0
    local total=${#tests[@]}
    
    for test_url in "${tests[@]}"; do
        if curl -f -s "$test_url" > /dev/null 2>&1; then
            log_success "✅ $test_url"
            ((passed++))
        else
            log_error "❌ $test_url"
        fi
    done
    
    if [[ $passed -eq $total ]]; then
        log_success "All smoke tests passed ($passed/$total)"
        return 0
    else
        log_error "Some smoke tests failed ($passed/$total)"
        return 1
    fi
}

rollback_deployment() {
    log "Rolling back deployment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would rollback deployment"
        return 0
    fi
    
    # Find previous image tag
    local previous_tag
    previous_tag=$(docker images --format "table {{.Tag}}" common-api | grep -v "$IMAGE_TAG" | head -1)
    
    if [[ -z "$previous_tag" ]]; then
        log_error "No previous image found for rollback"
        return 1
    fi
    
    log "Rolling back to tag: $previous_tag"
    
    # Deploy previous version
    export IMAGE_TAG="$previous_tag"
    docker-compose -f "$COMPOSE_FILE" up -d --remove-orphans
    
    # Wait for health check
    if wait_for_health; then
        log_success "Rollback completed successfully"
        return 0
    else
        log_error "Rollback failed health check"
        return 1
    fi
}

cleanup_old_resources() {
    log "Cleaning up old resources..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would cleanup old resources"
        return 0
    fi
    
    # Remove old images (keep last 5)
    docker images --format "table {{.ID}}\t{{.Tag}}" common-api | \
        tail -n +6 | \
        awk '{print $1}' | \
        xargs -r docker rmi
    
    # Remove unused containers
    docker container prune -f
    
    # Remove unused networks
    docker network prune -f
    
    # Remove unused volumes (be careful in production)
    if [[ "$ENVIRONMENT" != "production" ]]; then
        docker volume prune -f
    fi
    
    log_success "Cleanup completed"
}

record_deployment() {
    log "Recording deployment..."
    
    local deployment_record="{
        \"deployment_id\": \"$DEPLOYMENT_ID\",
        \"environment\": \"$ENVIRONMENT\",
        \"image_tag\": \"$IMAGE_TAG\",
        \"timestamp\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\",
        \"deployed_by\": \"$(whoami)\",
        \"git_commit\": \"$(git rev-parse HEAD 2>/dev/null || echo 'unknown')\",
        \"status\": \"completed\"
    }"
    
    echo "$deployment_record" > "/tmp/deployment-${DEPLOYMENT_ID}.json"
    log_success "Deployment recorded"
}

# Main deployment function
main() {
    log "Starting deployment to $ENVIRONMENT"
    log "Deployment ID: $DEPLOYMENT_ID"
    log "Image tag: $IMAGE_TAG"
    
    # Handle special operations
    if [[ "$CLEANUP" == "true" ]]; then
        cleanup_old_resources
        exit 0
    fi
    
    if [[ "$ROLLBACK" == "true" ]]; then
        rollback_deployment
        exit $?
    fi
    
    # Main deployment flow
    check_prerequisites
    
    # Build and push image
    build_image
    push_image
    
    # Run migrations
    run_migrations
    
    # Deploy services
    deploy_services
    
    # Wait for health check
    if ! wait_for_health; then
        log_error "Health check failed, attempting rollback..."
        if [[ "$ENVIRONMENT" == "production" ]]; then
            rollback_deployment
        fi
        exit 1
    fi
    
    # Run smoke tests
    if ! run_smoke_tests; then
        log_error "Smoke tests failed"
        if [[ "$ENVIRONMENT" == "production" ]]; then
            log_error "Production deployment failed, manual intervention required"
        fi
        exit 1
    fi
    
    # Record successful deployment
    record_deployment
    
    log_success "Deployment to $ENVIRONMENT completed successfully"
    log_success "Deployment ID: $DEPLOYMENT_ID"
    log_success "Image tag: $IMAGE_TAG"
    log_success "Log file: $LOG_FILE"
}

# Trap errors and cleanup
trap 'log_error "Deployment failed"; exit 1' ERR

# Run main function
main "$@"
