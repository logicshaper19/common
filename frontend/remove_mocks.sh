#!/bin/bash

# Script to remove all mock logic from admin clients

echo "Removing mock logic from admin clients..."

# Remove mock imports and providers from all admin client files
for file in src/api/admin/clients/*.ts; do
    if [ -f "$file" ]; then
        echo "Processing $file..."
        
        # Remove mock import lines
        sed -i '' '/import.*mock/d' "$file"
        sed -i '' '/MockProvider/d' "$file"
        
        # Remove mock provider declarations
        sed -i '' '/private mockProvider/d' "$file"
        
        # Remove try-catch blocks that fall back to mocks
        # This is more complex and needs manual review
        echo "  - Removed mock imports from $file"
    fi
done

echo "Mock removal complete. Please review files manually for remaining mock logic."
