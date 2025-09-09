/**
 * UI Components Index
 * Exports all UI components for easy importing
 */

// Core components
export { default as Button } from './Button';
export { default as Input } from './Input';
export { default as Select } from './Select';
export { default as Textarea } from './Textarea';
export { default as Modal } from './Modal';
export { default as LoadingSpinner } from './LoadingSpinner';
export { default as ErrorBoundary } from './ErrorBoundary';
export { default as Toast } from './Toast';

// Card components
export {
  Card,
  CardHeader,
  CardTitle,
  CardBody as CardContent,
  CardFooter,
  type CardProps,
  type CardHeaderProps,
  type CardTitleProps,
  type CardBodyProps as CardContentProps,
  type CardFooterProps
} from './Card';

// New components
export { Progress } from './Progress';
export { Tabs, TabsList, TabsTrigger, TabsContent } from './Tabs';
export { Alert, AlertDescription } from './Alert';
export { 
  Table, 
  TableHeader, 
  TableBody, 
  TableRow, 
  TableHead, 
  TableCell 
} from './Table';
export { default as Badge } from './Badge';
export { default as AnalyticsCard } from './AnalyticsCard';

// Re-export Card components with alternative names for compatibility
// CardContent is already exported above
