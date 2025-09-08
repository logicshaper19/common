#!/bin/bash

# Common MuleSoft Connector Build Script
# This script builds, tests, and packages the Common connector for distribution

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="Common MuleSoft Connector"
VERSION="1.0.0"
BUILD_DIR="target"
DIST_DIR="dist"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Building ${PROJECT_NAME} v${VERSION}${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to print status messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check if Maven is installed
if ! command -v mvn &> /dev/null; then
    print_error "Maven is not installed. Please install Maven 3.6+ to continue."
    exit 1
fi

# Check if Java is installed
if ! command -v java &> /dev/null; then
    print_error "Java is not installed. Please install Java 8+ to continue."
    exit 1
fi

# Check Java version
JAVA_VERSION=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}' | cut -d'.' -f1-2)
if [[ $(echo "$JAVA_VERSION < 1.8" | bc -l) -eq 1 ]]; then
    print_error "Java 8 or higher is required. Current version: $JAVA_VERSION"
    exit 1
fi

print_status "Prerequisites check passed"

# Clean previous builds
print_status "Cleaning previous builds..."
if [ -d "$BUILD_DIR" ]; then
    rm -rf "$BUILD_DIR"
fi
if [ -d "$DIST_DIR" ]; then
    rm -rf "$DIST_DIR"
fi
mkdir -p "$DIST_DIR"

# Validate project structure
print_status "Validating project structure..."
required_files=(
    "pom.xml"
    "src/main/java/com/common/connectors/CommonConnector.java"
    "src/main/java/com/common/connectors/internal/CommonOperations.java"
    "src/main/java/com/common/connectors/internal/connection/CommonConnectionProvider.java"
    "src/main/java/com/common/connectors/internal/connection/CommonConnection.java"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file missing: $file"
        exit 1
    fi
done

print_status "Project structure validation passed"

# Run tests
print_status "Running unit tests..."
mvn clean test -q
if [ $? -ne 0 ]; then
    print_error "Unit tests failed"
    exit 1
fi
print_status "Unit tests passed"

# Compile and package
print_status "Compiling and packaging connector..."
mvn clean package -DskipTests -q
if [ $? -ne 0 ]; then
    print_error "Build failed"
    exit 1
fi

# Check if JAR was created
JAR_FILE="$BUILD_DIR/common-mulesoft-connector-${VERSION}-mule-plugin.jar"
if [ ! -f "$JAR_FILE" ]; then
    print_error "Connector JAR not found: $JAR_FILE"
    exit 1
fi

print_status "Build completed successfully"

# Copy artifacts to distribution directory
print_status "Preparing distribution artifacts..."
cp "$JAR_FILE" "$DIST_DIR/"
cp "README.md" "$DIST_DIR/"
cp -r "src/main/resources/examples" "$DIST_DIR/"
cp -r "src/main/resources/dataweave" "$DIST_DIR/"

# Create installation guide
cat > "$DIST_DIR/INSTALLATION.md" << EOF
# Common MuleSoft Connector Installation Guide

## Quick Start

1. **Install from JAR**:
   - Copy \`common-mulesoft-connector-${VERSION}-mule-plugin.jar\` to your Mule application's \`lib\` directory
   - Restart your Mule application

2. **Configure Connection**:
   \`\`\`xml
   <common:config name="Common_Config">
       <common:connection 
           baseUrl="\${common.api.baseUrl}"
           clientId="\${common.api.clientId}"
           clientSecret="\${common.api.clientSecret}"
           companyId="\${common.api.companyId}" />
   </common:config>
   \`\`\`

3. **Use Operations**:
   \`\`\`xml
   <common:create-purchase-order config-ref="Common_Config" ... />
   \`\`\`

## Examples

See the \`examples/\` directory for complete flow examples.

## DataWeave Templates

See the \`dataweave/\` directory for SAP integration templates.

## Support

- Documentation: https://docs.common.co/connectors/mulesoft
- Support: support@common.co
EOF

# Generate checksums
print_status "Generating checksums..."
cd "$DIST_DIR"
sha256sum "common-mulesoft-connector-${VERSION}-mule-plugin.jar" > "common-mulesoft-connector-${VERSION}-mule-plugin.jar.sha256"
cd ..

# Create distribution package
print_status "Creating distribution package..."
PACKAGE_NAME="common-mulesoft-connector-${VERSION}"
tar -czf "${PACKAGE_NAME}.tar.gz" -C "$DIST_DIR" .
zip -r "${PACKAGE_NAME}.zip" "$DIST_DIR"/* > /dev/null

# Generate build report
print_status "Generating build report..."
cat > "BUILD_REPORT.md" << EOF
# Build Report - ${PROJECT_NAME} v${VERSION}

**Build Date**: $(date)
**Build Status**: SUCCESS
**Java Version**: $JAVA_VERSION
**Maven Version**: $(mvn -version | head -n 1)

## Artifacts Generated

- \`${JAR_FILE}\`
- \`${PACKAGE_NAME}.tar.gz\`
- \`${PACKAGE_NAME}.zip\`

## Distribution Contents

- Connector JAR file
- README.md documentation
- Installation guide
- Example flows
- DataWeave transformation templates
- SHA256 checksums

## Next Steps

1. Test the connector in a development environment
2. Deploy to Anypoint Exchange (if applicable)
3. Distribute to enterprise customers
4. Update documentation and release notes

## Quality Metrics

- Unit Tests: PASSED
- Code Coverage: $(mvn jacoco:report -q 2>/dev/null | grep -o '[0-9]*%' | tail -1 || echo "N/A")
- Build Time: $(date)

EOF

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Build Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
print_status "Artifacts created:"
echo "  - Connector JAR: $JAR_FILE"
echo "  - Distribution: ${PACKAGE_NAME}.tar.gz"
echo "  - Distribution: ${PACKAGE_NAME}.zip"
echo "  - Build Report: BUILD_REPORT.md"
echo ""
print_status "Next steps:"
echo "  1. Test the connector in Anypoint Studio"
echo "  2. Review the build report"
echo "  3. Deploy to target environments"
echo ""
echo -e "${BLUE}Happy integrating with Common! 🚀${NC}"
