#!/bin/bash

# Common Boomi Connector Build Script
# Packages the connector into a deployable Boomi Process Library package

set -e

# Configuration
CONNECTOR_NAME="common-boomi-connector"
VERSION="1.0.0"
BUILD_DIR="build"
PACKAGE_DIR="$BUILD_DIR/package"
DIST_DIR="dist"
PACKAGE_FILE="$CONNECTOR_NAME-$VERSION.zip"

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
        "package.json"
        "README.md"
        "process-library/connections/Common-API-Connection.xml"
        "process-library/processes/Create-Purchase-Order.xml"
        "process-library/processes/Propose-Changes.xml"
        "process-library/processes/Batch-ERP-Sync.xml"
        "process-library/maps/SAP-to-Common-PO-Map.xml"
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

# Function to validate XML files
validate_xml_files() {
    log_info "Validating XML files..."
    
    local xml_files=(
        process-library/connections/*.xml
        process-library/processes/*.xml
        process-library/maps/*.xml
    )
    
    local invalid_files=()
    
    for file_pattern in "${xml_files[@]}"; do
        for file in $file_pattern; do
            if [[ -f "$file" ]]; then
                if ! xmllint --noout "$file" 2>/dev/null; then
                    invalid_files+=("$file")
                fi
            fi
        done
    done
    
    if [[ ${#invalid_files[@]} -gt 0 ]]; then
        log_error "Invalid XML files found:"
        for file in "${invalid_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    log_success "All XML files are valid"
}

# Function to validate JSON files
validate_json_files() {
    log_info "Validating JSON files..."
    
    if ! python3 -m json.tool package.json > /dev/null 2>&1; then
        log_error "Invalid JSON in package.json"
        exit 1
    fi
    
    log_success "JSON files are valid"
}

# Function to create build directory structure
create_build_structure() {
    log_info "Creating build directory structure..."
    
    # Clean and create build directories
    rm -rf "$BUILD_DIR"
    mkdir -p "$PACKAGE_DIR"
    mkdir -p "$DIST_DIR"
    
    # Create package subdirectories
    mkdir -p "$PACKAGE_DIR/connections"
    mkdir -p "$PACKAGE_DIR/processes"
    mkdir -p "$PACKAGE_DIR/maps"
    mkdir -p "$PACKAGE_DIR/error-handlers"
    mkdir -p "$PACKAGE_DIR/utilities"
    mkdir -p "$PACKAGE_DIR/documentation"
    mkdir -p "$PACKAGE_DIR/examples"
    
    log_success "Build directory structure created"
}

# Function to copy connector files
copy_connector_files() {
    log_info "Copying connector files..."
    
    # Copy main files
    cp package.json "$PACKAGE_DIR/"
    cp README.md "$PACKAGE_DIR/"
    
    # Copy process library components
    if [[ -d "process-library/connections" ]]; then
        cp process-library/connections/*.xml "$PACKAGE_DIR/connections/" 2>/dev/null || true
    fi
    
    if [[ -d "process-library/processes" ]]; then
        cp process-library/processes/*.xml "$PACKAGE_DIR/processes/" 2>/dev/null || true
    fi
    
    if [[ -d "process-library/maps" ]]; then
        cp process-library/maps/*.xml "$PACKAGE_DIR/maps/" 2>/dev/null || true
    fi
    
    if [[ -d "process-library/error-handlers" ]]; then
        cp process-library/error-handlers/*.xml "$PACKAGE_DIR/error-handlers/" 2>/dev/null || true
    fi
    
    if [[ -d "process-library/utilities" ]]; then
        cp process-library/utilities/*.xml "$PACKAGE_DIR/utilities/" 2>/dev/null || true
    fi
    
    # Copy documentation if exists
    if [[ -d "documentation" ]]; then
        cp documentation/* "$PACKAGE_DIR/documentation/" 2>/dev/null || true
    fi
    
    # Copy examples if exists
    if [[ -d "examples" ]]; then
        cp examples/* "$PACKAGE_DIR/examples/" 2>/dev/null || true
    fi
    
    log_success "Connector files copied"
}

# Function to generate manifest file
generate_manifest() {
    log_info "Generating manifest file..."
    
    cat > "$PACKAGE_DIR/MANIFEST.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<ProcessLibraryManifest xmlns="http://www.boomi.com/manifest">
    <Name>$CONNECTOR_NAME</Name>
    <Version>$VERSION</Version>
    <Description>Common Supply Chain Transparency Platform Connector for Dell Boomi</Description>
    <Vendor>Common</Vendor>
    <Category>Supply Chain</Category>
    <SubCategory>Transparency</SubCategory>
    <MinimumBoomiVersion>2.4.0</MinimumBoomiVersion>
    <BuildDate>$(date -u +"%Y-%m-%dT%H:%M:%SZ")</BuildDate>
    <SupportLevel>ENTERPRISE</SupportLevel>
    <Certification>BOOMI_CERTIFIED</Certification>
    
    <Components>
        <Connections>
            <Connection name="Common API Connection" file="connections/Common-API-Connection.xml"/>
        </Connections>
        
        <Processes>
            <Process name="Create Purchase Order" file="processes/Create-Purchase-Order.xml"/>
            <Process name="Propose Changes" file="processes/Propose-Changes.xml"/>
            <Process name="Batch ERP Sync" file="processes/Batch-ERP-Sync.xml"/>
        </Processes>
        
        <Maps>
            <Map name="SAP to Common PO Map" file="maps/SAP-to-Common-PO-Map.xml"/>
        </Maps>
    </Components>
    
    <Dependencies>
        <Dependency type="connector" name="http-client" version=">=2.4.0"/>
        <Dependency type="connector" name="email" version=">=2.4.0"/>
    </Dependencies>
    
    <Configuration>
        <RequiredProperties>
            <Property name="baseUrl" description="Common API base URL"/>
            <Property name="clientId" description="OAuth client ID"/>
            <Property name="clientSecret" description="OAuth client secret"/>
            <Property name="companyId" description="Company UUID"/>
        </RequiredProperties>
    </Configuration>
</ProcessLibraryManifest>
EOF
    
    log_success "Manifest file generated"
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
    echo "  Name: $CONNECTOR_NAME"
    echo "  Version: $VERSION"
    echo "  Package File: $DIST_DIR/$PACKAGE_FILE"
    
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
    log_info "Starting build process for $CONNECTOR_NAME v$VERSION"
    
    # Validation steps
    check_required_files
    validate_json_files
    
    # Only validate XML if xmllint is available
    if command -v xmllint > /dev/null; then
        validate_xml_files
    else
        log_warning "xmllint not found, skipping XML validation"
    fi
    
    # Build steps
    create_build_structure
    copy_connector_files
    generate_manifest
    create_package
    generate_checksums
    
    # Display results
    display_package_info
    
    log_success "Build completed successfully!"
    log_info "Package ready for deployment: $DIST_DIR/$PACKAGE_FILE"
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
        validate_json_files
        if command -v xmllint > /dev/null; then
            validate_xml_files
        fi
        log_success "Validation completed"
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [clean|validate]"
        echo "  clean    - Clean build directories"
        echo "  validate - Run validation only"
        echo "  (no args) - Full build"
        exit 1
        ;;
esac
