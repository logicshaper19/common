#!/bin/bash

# Common SAP Integration Build Script
# Creates transport package for SAP system deployment

set -e

# Configuration
INTEGRATION_NAME="common-sap-integration"
VERSION="1.0.0"
BUILD_DIR="build"
TRANSPORT_DIR="$BUILD_DIR/transport"
PACKAGE_DIR="$BUILD_DIR/package"
DIST_DIR="dist"
PACKAGE_FILE="$INTEGRATION_NAME-$VERSION.zip"

# SAP Transport Configuration
TRANSPORT_LAYER="ZCOM"
DEVELOPMENT_CLASS="ZCOMMON"
TRANSPORT_REQUEST=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if required files exist
check_required_files() {
    log_info "Checking required files..."
    
    local required_files=(
        "README.md"
        "abap/function-modules/Z_COMMON_CREATE_PO.abap"
        "abap/function-modules/Z_COMMON_PROPOSE_AMENDMENT.abap"
        "abap/includes/ZCOMMON_UTILITIES.abap"
        "ddic/tables/ZCOMMON_TABLES.ddl"
        "idoc/segments/ZCOMMON_ORDERS01.txt"
        "odata/ZCL_COMMON_PO_DPC_EXT.abap"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    log_success "All required files found"
}

# Function to validate ABAP syntax (if available)
validate_abap_syntax() {
    log_info "Validating ABAP syntax..."
    
    # This would require SAP system connection for real validation
    # For now, just check basic file structure
    
    local abap_files=(
        abap/function-modules/*.abap
        abap/includes/*.abap
        odata/*.abap
    )
    
    for file_pattern in "${abap_files[@]}"; do
        for file in $file_pattern; do
            if [[ -f "$file" ]]; then
                # Basic syntax check - look for required ABAP keywords
                if ! grep -q "FUNCTION\|CLASS\|FORM\|METHOD" "$file"; then
                    log_warning "File $file may not contain valid ABAP code"
                fi
            fi
        done
    done
    
    log_success "ABAP syntax validation completed"
}

# Function to create build directory structure
create_build_structure() {
    log_info "Creating build directory structure..."
    
    # Clean and create build directories
    rm -rf "$BUILD_DIR"
    mkdir -p "$TRANSPORT_DIR"
    mkdir -p "$PACKAGE_DIR"
    mkdir -p "$DIST_DIR"
    
    # Create transport subdirectories
    mkdir -p "$TRANSPORT_DIR/cofiles"
    mkdir -p "$TRANSPORT_DIR/data"
    mkdir -p "$TRANSPORT_DIR/abap"
    mkdir -p "$TRANSPORT_DIR/ddic"
    mkdir -p "$TRANSPORT_DIR/idoc"
    mkdir -p "$TRANSPORT_DIR/odata"
    
    # Create package subdirectories
    mkdir -p "$PACKAGE_DIR/abap/function-modules"
    mkdir -p "$PACKAGE_DIR/abap/includes"
    mkdir -p "$PACKAGE_DIR/abap/programs"
    mkdir -p "$PACKAGE_DIR/ddic/tables"
    mkdir -p "$PACKAGE_DIR/ddic/structures"
    mkdir -p "$PACKAGE_DIR/idoc/segments"
    mkdir -p "$PACKAGE_DIR/idoc/message-types"
    mkdir -p "$PACKAGE_DIR/odata/services"
    mkdir -p "$PACKAGE_DIR/configuration"
    mkdir -p "$PACKAGE_DIR/documentation"
    
    log_success "Build directory structure created"
}

# Function to copy integration files
copy_integration_files() {
    log_info "Copying integration files..."
    
    # Copy main files
    cp README.md "$PACKAGE_DIR/"
    
    # Copy ABAP components
    if [[ -d "abap/function-modules" ]]; then
        cp abap/function-modules/*.abap "$PACKAGE_DIR/abap/function-modules/" 2>/dev/null || true
    fi
    
    if [[ -d "abap/includes" ]]; then
        cp abap/includes/*.abap "$PACKAGE_DIR/abap/includes/" 2>/dev/null || true
    fi
    
    if [[ -d "abap/programs" ]]; then
        cp abap/programs/*.abap "$PACKAGE_DIR/abap/programs/" 2>/dev/null || true
    fi
    
    # Copy DDIC components
    if [[ -d "ddic/tables" ]]; then
        cp ddic/tables/*.ddl "$PACKAGE_DIR/ddic/tables/" 2>/dev/null || true
    fi
    
    if [[ -d "ddic/structures" ]]; then
        cp ddic/structures/*.ddl "$PACKAGE_DIR/ddic/structures/" 2>/dev/null || true
    fi
    
    # Copy IDoc components
    if [[ -d "idoc/segments" ]]; then
        cp idoc/segments/*.txt "$PACKAGE_DIR/idoc/segments/" 2>/dev/null || true
    fi
    
    if [[ -d "idoc/message-types" ]]; then
        cp idoc/message-types/*.txt "$PACKAGE_DIR/idoc/message-types/" 2>/dev/null || true
    fi
    
    # Copy OData components
    if [[ -d "odata" ]]; then
        cp odata/*.abap "$PACKAGE_DIR/odata/services/" 2>/dev/null || true
    fi
    
    # Copy configuration files
    if [[ -d "configuration" ]]; then
        cp configuration/* "$PACKAGE_DIR/configuration/" 2>/dev/null || true
    fi
    
    # Copy documentation
    if [[ -d "documentation" ]]; then
        cp documentation/* "$PACKAGE_DIR/documentation/" 2>/dev/null || true
    fi
    
    log_success "Integration files copied"
}

# Function to generate transport files
generate_transport_files() {
    log_info "Generating transport files..."
    
    # Generate transport request (this would normally be done in SAP system)
    if [[ -z "$TRANSPORT_REQUEST" ]]; then
        TRANSPORT_REQUEST="ZCOMK900001"
        log_warning "Using default transport request: $TRANSPORT_REQUEST"
    fi
    
    # Create transport control file
    cat > "$TRANSPORT_DIR/cofiles/K$TRANSPORT_REQUEST" << EOF
#Transport request $TRANSPORT_REQUEST
#Created: $(date -u +"%Y%m%d %H%M%S")
#Description: Common SAP Integration Package v$VERSION
#Development class: $DEVELOPMENT_CLASS
#Transport layer: $TRANSPORT_LAYER
EOF
    
    # Create transport data file header
    cat > "$TRANSPORT_DIR/data/R$TRANSPORT_REQUEST" << EOF
#Transport data for request $TRANSPORT_REQUEST
#Common SAP Integration Package
#Version: $VERSION
#Build date: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
EOF
    
    # Copy ABAP objects to transport directory
    cp -r abap/* "$TRANSPORT_DIR/abap/" 2>/dev/null || true
    cp -r ddic/* "$TRANSPORT_DIR/ddic/" 2>/dev/null || true
    cp -r idoc/* "$TRANSPORT_DIR/idoc/" 2>/dev/null || true
    cp -r odata/* "$TRANSPORT_DIR/odata/" 2>/dev/null || true
    
    log_success "Transport files generated"
}

# Function to create configuration templates
create_configuration_templates() {
    log_info "Creating configuration templates..."
    
    # Create configuration template
    cat > "$PACKAGE_DIR/configuration/config-template.txt" << EOF
# Common SAP Integration Configuration Template
# Copy this file to config.txt and customize for your environment

# API Configuration
API_BASE_URL=https://api.common.co
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here
AUTH_URL=https://api.common.co/api/v1/auth/token

# SAP Configuration
SAP_CLIENT=100
SAP_LANGUAGE=EN
DEVELOPMENT_CLASS=ZCOMMON
TRANSPORT_LAYER=ZCOM

# Integration Settings
API_TIMEOUT=30
MAX_RETRIES=3
BATCH_SIZE=100
LOG_LEVEL=INFO
AUDIT_ENABLED=true

# Notification Settings
NOTIFICATION_EMAIL=admin@company.com
ERROR_NOTIFICATION=true
SUCCESS_NOTIFICATION=false

# Performance Settings
CONNECTION_POOL_SIZE=10
CACHE_ENABLED=true
CACHE_TTL_MINUTES=60
PARALLEL_PROCESSING=true
MAX_CONCURRENT_REQUESTS=5
EOF

    # Create field mapping template
    cat > "$PACKAGE_DIR/configuration/field-mappings.csv" << EOF
SourceSystem,TargetSystem,SourceField,TargetField,MappingType,LookupTable,DefaultValue,Required
SAP,COMMON,BUKRS,buyer_company_id,LOOKUP,ZCOMMON_COMPANY,,true
SAP,COMMON,LIFNR,seller_company_id,LOOKUP,ZCOMMON_VENDOR,,true
SAP,COMMON,MATNR,product_id,LOOKUP,ZCOMMON_MATERIAL,,true
SAP,COMMON,MENGE,quantity,DIRECT,,,true
SAP,COMMON,NETPR,unit_price,DIRECT,,,true
SAP,COMMON,MEINS,unit,LOOKUP,ZCOMMON_UOM,kg,true
SAP,COMMON,EINDT,delivery_date,DATE_CONVERSION,,,true
SAP,COMMON,WERKS,delivery_location,LOOKUP,ZCOMMON_PLANT,,true
SAP,COMMON,EBELN,po_number,DIRECT,,,false
SAP,COMMON,TXZOL,notes,DIRECT,,,false
EOF

    # Create lookup data template
    cat > "$PACKAGE_DIR/configuration/lookup-data.csv" << EOF
LookupTable,SourceValue,TargetValue,Description
ZCOMMON_COMPANY,1000,company-uuid-1000,Main Company
ZCOMMON_COMPANY,2000,company-uuid-2000,Subsidiary A
ZCOMMON_VENDOR,VENDOR001,vendor-uuid-001,Primary Supplier
ZCOMMON_VENDOR,VENDOR002,vendor-uuid-002,Secondary Supplier
ZCOMMON_MATERIAL,MATERIAL001,product-uuid-001,Raw Material A
ZCOMMON_MATERIAL,MATERIAL002,product-uuid-002,Raw Material B
ZCOMMON_UOM,KG,kg,Kilogram
ZCOMMON_UOM,G,g,Gram
ZCOMMON_UOM,LB,lb,Pound
ZCOMMON_UOM,PC,piece,Piece
ZCOMMON_PLANT,PLANT001,Warehouse A - New York,Main Warehouse
ZCOMMON_PLANT,PLANT002,Warehouse B - Los Angeles,West Coast Warehouse
EOF

    log_success "Configuration templates created"
}

# Function to generate installation guide
generate_installation_guide() {
    log_info "Generating installation guide..."
    
    cat > "$PACKAGE_DIR/INSTALLATION_GUIDE.md" << EOF
# Common SAP Integration Installation Guide

## Prerequisites

- SAP ECC 6.0 EHP7 or SAP S/4HANA 1809 or higher
- ABAP development authorization
- SAP Gateway access (for OData services)
- Network connectivity to api.common.co (HTTPS/443)
- Common API credentials (Client ID and Client Secret)

## Installation Steps

### 1. Import Transport

1. Copy transport files to SAP transport directory:
   - Copy cofiles/K$TRANSPORT_REQUEST to /usr/sap/trans/cofiles/
   - Copy data/R$TRANSPORT_REQUEST to /usr/sap/trans/data/

2. Import transport using STMS:
   - Transaction: STMS
   - Import queue → Add transport → $TRANSPORT_REQUEST
   - Import transport

3. Activate all imported objects:
   - Transaction: SE80
   - Check activation log for any errors

### 2. Configure RFC Destinations

1. Create HTTP destination for Common API:
   - Transaction: SM59
   - Create new destination: COMMON_API_PROD
   - Connection Type: G (HTTP to External Server)
   - Target Host: api.common.co
   - Service No: 443
   - Path Prefix: /api/v1

2. Configure SSL:
   - Import Common API SSL certificate
   - Configure SSL client identity

### 3. Set Up Configuration Tables

1. Maintain configuration parameters:
   - Transaction: SM30
   - Table: ZCOMMON_CONFIG
   - Import configuration from config-template.txt

2. Maintain field mappings:
   - Transaction: SM30
   - Table: ZCOMMON_MAPPING
   - Import mappings from field-mappings.csv

3. Maintain lookup data:
   - Import company mappings to ZCOMMON_COMPANY_MAP
   - Import vendor mappings to ZCOMMON_VENDOR_MAP
   - Import material mappings to ZCOMMON_MATERIAL_MAP
   - Import UOM mappings to ZCOMMON_UOM_MAP

### 4. Test Integration

1. Test RFC functions:
   - Transaction: SE37
   - Test Z_COMMON_CREATE_PO
   - Test Z_COMMON_PROPOSE_AMENDMENT

2. Test OData service:
   - Transaction: /IWFND/MAINT_SERVICE
   - Activate ZCOMMON_PO_SRV service
   - Test service endpoints

3. Test IDoc processing:
   - Transaction: WE19
   - Create test IDoc with message type ZCOMMON_ORDERS
   - Process and verify results

### 5. Configure Monitoring

1. Set up background jobs:
   - Transaction: SM36
   - Schedule batch synchronization jobs
   - Configure error notification jobs

2. Configure monitoring:
   - Transaction: SM30
   - Table: ZCOMMON_CONFIG
   - Enable monitoring and alerting

## Post-Installation

1. Review error logs in ZCOMMON_LOG
2. Monitor performance metrics
3. Set up regular maintenance procedures
4. Train users on new functionality

## Support

For technical support, contact: support@common.co
Documentation: https://docs.common.co/connectors/sap
EOF

    log_success "Installation guide generated"
}

# Function to create package archive
create_package() {
    log_info "Creating package archive..."
    
    cd "$PACKAGE_DIR"
    zip -r "../../$DIST_DIR/$PACKAGE_FILE" . -x "*.DS_Store" "*.git*"
    cd - > /dev/null
    
    log_success "Package created: $DIST_DIR/$PACKAGE_FILE"
}

# Function to generate checksums
generate_checksums() {
    log_info "Generating checksums..."
    
    cd "$DIST_DIR"
    
    # Generate MD5 checksum
    if command -v md5sum > /dev/null; then
        md5sum "$PACKAGE_FILE" > "$PACKAGE_FILE.md5"
    elif command -v md5 > /dev/null; then
        md5 "$PACKAGE_FILE" | sed 's/MD5 (\(.*\)) = \(.*\)/\2  \1/' > "$PACKAGE_FILE.md5"
    fi
    
    # Generate SHA256 checksum
    if command -v sha256sum > /dev/null; then
        sha256sum "$PACKAGE_FILE" > "$PACKAGE_FILE.sha256"
    elif command -v shasum > /dev/null; then
        shasum -a 256 "$PACKAGE_FILE" > "$PACKAGE_FILE.sha256"
    fi
    
    cd - > /dev/null
    
    log_success "Checksums generated"
}

# Function to display package information
display_package_info() {
    log_info "Package Information:"
    echo "  Name: $INTEGRATION_NAME"
    echo "  Version: $VERSION"
    echo "  Package File: $DIST_DIR/$PACKAGE_FILE"
    echo "  Transport Request: $TRANSPORT_REQUEST"
    echo "  Development Class: $DEVELOPMENT_CLASS"
    
    if [[ -f "$DIST_DIR/$PACKAGE_FILE" ]]; then
        local size=$(du -h "$DIST_DIR/$PACKAGE_FILE" | cut -f1)
        echo "  Size: $size"
    fi
    
    if [[ -f "$DIST_DIR/$PACKAGE_FILE.md5" ]]; then
        echo "  MD5: $(cat "$DIST_DIR/$PACKAGE_FILE.md5" | cut -d' ' -f1)"
    fi
    
    if [[ -f "$DIST_DIR/$PACKAGE_FILE.sha256" ]]; then
        echo "  SHA256: $(cat "$DIST_DIR/$PACKAGE_FILE.sha256" | cut -d' ' -f1)"
    fi
}

# Main build function
main() {
    log_info "Starting build process for $INTEGRATION_NAME v$VERSION"
    
    # Validation steps
    check_required_files
    validate_abap_syntax
    
    # Build steps
    create_build_structure
    copy_integration_files
    generate_transport_files
    create_configuration_templates
    generate_installation_guide
    create_package
    generate_checksums
    
    # Display results
    display_package_info
    
    log_success "Build completed successfully!"
    log_info "Package ready for SAP deployment: $DIST_DIR/$PACKAGE_FILE"
}

# Handle command line arguments
case "${1:-}" in
    "clean")
        log_info "Cleaning build directories..."
        rm -rf "$BUILD_DIR" "$DIST_DIR"
        log_success "Clean completed"
        ;;
    "validate")
        log_info "Running validation only..."
        check_required_files
        validate_abap_syntax
        log_success "Validation completed"
        ;;
    "transport")
        log_info "Generating transport files only..."
        create_build_structure
        generate_transport_files
        log_success "Transport files generated in $TRANSPORT_DIR"
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [clean|validate|transport]"
        echo "  clean     - Clean build directories"
        echo "  validate  - Run validation only"
        echo "  transport - Generate transport files only"
        echo "  (no args) - Full build"
        exit 1
        ;;
esac
