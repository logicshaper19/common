# SEMA Design System Integration Guide

## Project Context 🏗️

**Backend Project**: This is a FastAPI (Python) backend for the Common supply chain transparency platform.
**Design System**: Your SEMA Design System is a React/TypeScript component library.

## Integration Strategy

Since this is a Python backend project, the design system will be used by your **frontend application** (separate from this backend). Here's how to set it up properly:

### 2. Available Components
Based on your design system, you have access to:
- **Button** - Flexible button component with multiple variants
- **Card** - Container component with CardHeader, CardBody, CardFooter
- **Badge** - Status and label component with dismissible option

### 3. Design Tokens
Your design system includes:
- Color palette with semantic variants
- Typography (Inter font family)
- Spacing scale
- Shadow system
- Animation presets

## How to Use

### Option 1: Import from Built Package (Recommended for Production)
```tsx
import { Button, Card, CardHeader, CardBody, Badge } from 'sema-design-system';
import 'sema-design-system/styles';

function MyComponent() {
  return (
    <Card>
      <CardHeader>
        <h2>Supply Chain Dashboard</h2>
        <Badge variant="success">Active</Badge>
      </CardHeader>
      <CardBody>
        <p>Content here...</p>
        <Button variant="primary">Action</Button>
      </CardBody>
    </Card>
  );
}
```

### Option 2: Import from Source (Better for Development)
```tsx
// Direct import from source files (bypasses build issues)
import { Button } from '../semamvp-1/sema-design-system/src/components/Button';
import { Card } from '../semamvp-1/sema-design-system/src/components/Card';
```

### Option 3: Use Tailwind Classes Directly
Since your design system is built with Tailwind CSS, you can also use the utility classes directly:

```tsx
function Dashboard() {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">
        Purchase Orders
      </h2>
      <button className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">
        View Details
      </button>
    </div>
  );
}
```

## Troubleshooting

### Build Issues
If you encounter import errors, the design system may need to be rebuilt:
```bash
cd /Users/elisha/semamvp-1/sema-design-system
npm run build
```

### Alternative Setup
If the npm link approach has issues, you can install it as a local dependency:
```bash
npm install file:../semamvp-1/sema-design-system
```

## Next Steps

1. **Set up Tailwind CSS** in your project to use the design tokens
2. **Create your first component** using the design system
3. **Configure your build process** to include the design system styles
4. **Test the components** in your application

## Example Files Created

- `example-usage.tsx` - Shows how to use the components
- `import-from-source.tsx` - Example dashboard using Tailwind classes
- `test-import.js` - Simple import test

## Design System Info

- **Name**: SEMA Design System
- **Version**: 1.0.0
- **Built with**: React, TypeScript, Tailwind CSS
- **Features**: Responsive design, accessibility focused, dark mode ready

Your design system is now ready to use in your Common platform project! 🎉
