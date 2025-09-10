#!/bin/bash

# Blue-Green Deployment Traffic Switching Script
# This script handles traffic switching between blue and green environments

set -euo pipefail

# Configuration
NAMESPACE="common-platform"
SERVICE_NAME="common-api-service"
BLUE_DEPLOYMENT="common-api-blue"
GREEN_DEPLOYMENT="common-api-green"
HEALTH_CHECK_URL="https://api.common.com/health"
HEALTH_CHECK_TIMEOUT=300
ROLLBACK_TIMEOUT=120

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Function to check if kubectl is available
check_prerequisites() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Function to get current active environment
get_current_environment() {
    local current_selector
    current_selector=$(kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.selector.version}' 2>/dev/null || echo "")
    
    if [[ "$current_selector" == "blue" ]]; then
        echo "blue"
    elif [[ "$current_selector" == "green" ]]; then
        echo "green"
    else
        echo "unknown"
    fi
}

# Function to get target environment
get_target_environment() {
    local current_env="$1"
    
    if [[ "$current_env" == "blue" ]]; then
        echo "green"
    elif [[ "$current_env" == "green" ]]; then
        echo "blue"
    else
        log_error "Cannot determine target environment from current: $current_env"
        exit 1
    fi
}

# Function to scale deployment
scale_deployment() {
    local deployment="$1"
    local replicas="$2"
    
    log "Scaling $deployment to $replicas replicas..."
    
    kubectl scale deployment "$deployment" -n "$NAMESPACE" --replicas="$replicas"
    
    if [[ "$replicas" -gt 0 ]]; then
        log "Waiting for $deployment to be ready..."
        kubectl rollout status deployment "$deployment" -n "$NAMESPACE" --timeout=300s
    fi
    
    log_success "$deployment scaled to $replicas replicas"
}

# Function to perform health check
perform_health_check() {
    local url="$1"
    local timeout="$2"
    local start_time
    local elapsed_time
    
    start_time=$(date +%s)
    
    log "Performing health check on $url (timeout: ${timeout}s)..."
    
    while true; do
        elapsed_time=$(($(date +%s) - start_time))
        
        if [[ $elapsed_time -gt $timeout ]]; then
            log_error "Health check timed out after ${timeout}s"
            return 1
        fi
        
        if curl -f -s --max-time 10 "$url" > /dev/null 2>&1; then
            log_success "Health check passed (${elapsed_time}s)"
            return 0
        fi
        
        log "Health check failed, retrying in 10s... (elapsed: ${elapsed_time}s)"
        sleep 10
    done
}

# Function to switch traffic
switch_traffic() {
    local target_env="$1"
    
    log "Switching traffic to $target_env environment..."
    
    kubectl patch service "$SERVICE_NAME" -n "$NAMESPACE" \
        -p '{"spec":{"selector":{"version":"'$target_env'"}}}'
    
    # Wait a moment for the change to propagate
    sleep 5
    
    log_success "Traffic switched to $target_env environment"
}

# Function to update HPA target
update_hpa_target() {
    local target_deployment="$1"
    
    log "Updating HPA target to $target_deployment..."
    
    kubectl patch hpa common-api-hpa -n "$NAMESPACE" \
        -p '{"spec":{"scaleTargetRef":{"name":"'$target_deployment'"}}}'
    
    log_success "HPA target updated to $target_deployment"
}

# Function to perform blue-green deployment
deploy_blue_green() {
    local new_image="$1"
    local dry_run="${2:-false}"
    
    if [[ "$dry_run" == "true" ]]; then
        log "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Get current environment
    local current_env
    current_env=$(get_current_environment)
    
    if [[ "$current_env" == "unknown" ]]; then
        log_error "Cannot determine current environment"
        exit 1
    fi
    
    local target_env
    target_env=$(get_target_environment "$current_env")
    
    log "Current environment: $current_env"
    log "Target environment: $target_env"
    log "New image: $new_image"
    
    if [[ "$dry_run" == "true" ]]; then
        log "DRY RUN: Would deploy $new_image to $target_env environment"
        return 0
    fi
    
    # Update target deployment with new image
    local target_deployment="common-api-$target_env"
    
    log "Updating $target_deployment with new image..."
    kubectl set image deployment "$target_deployment" -n "$NAMESPACE" \
        common-api="$new_image"
    
    # Scale up target environment
    scale_deployment "$target_deployment" 4
    
    # Perform health check on target environment
    if ! perform_health_check "$HEALTH_CHECK_URL" "$HEALTH_CHECK_TIMEOUT"; then
        log_error "Health check failed for $target_env environment"
        log "Rolling back..."
        scale_deployment "$target_deployment" 0
        exit 1
    fi
    
    # Switch traffic to target environment
    switch_traffic "$target_env"
    
    # Update HPA target
    update_hpa_target "$target_deployment"
    
    # Perform final health check
    if ! perform_health_check "$HEALTH_CHECK_URL" 60; then
        log_error "Final health check failed after traffic switch"
        log "Rolling back..."
        rollback_deployment "$current_env"
        exit 1
    fi
    
    # Scale down old environment
    local old_deployment="common-api-$current_env"
    scale_deployment "$old_deployment" 0
    
    log_success "Blue-green deployment completed successfully!"
    log_success "Active environment: $target_env"
    log_success "Image: $new_image"
}

# Function to rollback deployment
rollback_deployment() {
    local rollback_env="$1"
    
    log "Rolling back to $rollback_env environment..."
    
    # Switch traffic back
    switch_traffic "$rollback_env"
    
    # Update HPA target
    update_hpa_target "common-api-$rollback_env"
    
    # Ensure rollback environment is scaled up
    scale_deployment "common-api-$rollback_env" 4
    
    # Perform health check
    if perform_health_check "$HEALTH_CHECK_URL" "$ROLLBACK_TIMEOUT"; then
        log_success "Rollback completed successfully"
    else
        log_error "Rollback health check failed - manual intervention required"
        exit 1
    fi
}

# Function to show current status
show_status() {
    local current_env
    current_env=$(get_current_environment)
    
    echo "=== Blue-Green Deployment Status ==="
    echo "Current active environment: $current_env"
    echo ""
    
    echo "Blue environment:"
    kubectl get deployment "$BLUE_DEPLOYMENT" -n "$NAMESPACE" -o wide 2>/dev/null || echo "  Not found"
    echo ""
    
    echo "Green environment:"
    kubectl get deployment "$GREEN_DEPLOYMENT" -n "$NAMESPACE" -o wide 2>/dev/null || echo "  Not found"
    echo ""
    
    echo "Service configuration:"
    kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o wide 2>/dev/null || echo "  Not found"
}

# Main function
main() {
    local command="${1:-}"
    
    case "$command" in
        "deploy")
            if [[ $# -lt 2 ]]; then
                echo "Usage: $0 deploy <image_tag> [--dry-run]"
                exit 1
            fi
            
            local image_tag="$2"
            local dry_run="false"
            
            if [[ "${3:-}" == "--dry-run" ]]; then
                dry_run="true"
            fi
            
            check_prerequisites
            deploy_blue_green "$image_tag" "$dry_run"
            ;;
        
        "rollback")
            if [[ $# -lt 2 ]]; then
                echo "Usage: $0 rollback <environment>"
                echo "Environment should be 'blue' or 'green'"
                exit 1
            fi
            
            local rollback_env="$2"
            
            if [[ "$rollback_env" != "blue" && "$rollback_env" != "green" ]]; then
                log_error "Invalid environment: $rollback_env. Must be 'blue' or 'green'"
                exit 1
            fi
            
            check_prerequisites
            rollback_deployment "$rollback_env"
            ;;
        
        "status")
            check_prerequisites
            show_status
            ;;
        
        "switch")
            if [[ $# -lt 2 ]]; then
                echo "Usage: $0 switch <environment>"
                echo "Environment should be 'blue' or 'green'"
                exit 1
            fi
            
            local target_env="$2"
            
            if [[ "$target_env" != "blue" && "$target_env" != "green" ]]; then
                log_error "Invalid environment: $target_env. Must be 'blue' or 'green'"
                exit 1
            fi
            
            check_prerequisites
            switch_traffic "$target_env"
            update_hpa_target "common-api-$target_env"
            ;;
        
        *)
            echo "Usage: $0 {deploy|rollback|status|switch}"
            echo ""
            echo "Commands:"
            echo "  deploy <image_tag> [--dry-run]  - Deploy new image using blue-green strategy"
            echo "  rollback <environment>          - Rollback to specified environment (blue|green)"
            echo "  status                          - Show current deployment status"
            echo "  switch <environment>            - Switch traffic to specified environment"
            echo ""
            echo "Examples:"
            echo "  $0 deploy registry.common.com/common-api:v1.2.3"
            echo "  $0 deploy registry.common.com/common-api:v1.2.3 --dry-run"
            echo "  $0 rollback blue"
            echo "  $0 status"
            echo "  $0 switch green"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
