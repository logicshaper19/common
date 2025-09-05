import React from 'react';
// Import components from your design system
import { Button, Card, CardHeader, CardBody, CardFooter, Badge } from 'sema-design-system';
// Import styles
import 'sema-design-system/styles';

export default function ExampleUsage() {
  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">SEMA Design System Example</h1>

      <Card>
        <CardHeader>
          <h2 className="text-xl">Supply Chain Dashboard</h2>
          <Badge variant="success">Active</Badge>
        </CardHeader>
        <CardBody>
          <p className="text-gray-600 mb-4">
            Welcome to the Common platform - your supply chain transparency solution.
          </p>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Transparency Score:</span>
              <Badge variant="primary">85%</Badge>
            </div>
            <div className="flex justify-between">
              <span>Active POs:</span>
              <Badge variant="secondary">12</Badge>
            </div>
          </div>
        </CardBody>
        <CardFooter>
          <div className="flex gap-4">
            <Button variant="primary">View Details</Button>
            <Button variant="secondary">Export Data</Button>
          </div>
        </CardFooter>
      </Card>

      <div className="flex gap-4 flex-wrap">
        <Button variant="primary">Primary Action</Button>
        <Button variant="secondary">Secondary Action</Button>
        <Button variant="outline">Outline Button</Button>
        <Badge variant="success">Success</Badge>
        <Badge variant="warning">Warning</Badge>
        <Badge variant="error">Error</Badge>
      </div>
    </div>
  );
}
