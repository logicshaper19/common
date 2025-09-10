/**
 * Utility functions for the Common Supply Chain Platform frontend
 */
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines class names using clsx and tailwind-merge
 * This ensures Tailwind classes are properly merged and deduplicated
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Get color class for transparency score
 */
export function getTransparencyColor(score: number): string {
  if (score >= 90) return 'text-success-600';
  if (score >= 80) return 'text-success-500';
  if (score >= 70) return 'text-warning-500';
  if (score >= 60) return 'text-warning-600';
  return 'text-error-600';
}

/**
 * Format transparency score for display
 */
export function formatTransparency(score: number): string {
  return `${score.toFixed(1)}%`;
}

/**
 * Calculate transparency trend
 */
export function calculateTrend(current: number, previous: number): {
  value: number;
  direction: 'up' | 'down' | 'stable';
  percentage: number;
} {
  const diff = current - previous;
  const percentage = previous > 0 ? (diff / previous) * 100 : 0;

  return {
    value: diff,
    direction: diff > 0 ? 'up' : diff < 0 ? 'down' : 'stable',
    percentage: Math.abs(percentage),
  };
}

/**
 * Format currency values
 */
export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
}

/**
 * Format numbers with proper locale formatting
 */
export function formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat('en-US', options).format(value);
}

/**
 * Format dates in a user-friendly way
 */
export function formatDate(date: string | Date, options?: Intl.DateTimeFormatOptions): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };
  
  return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(dateObj);
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);
  
  const intervals = [
    { label: 'year', seconds: 31536000 },
    { label: 'month', seconds: 2592000 },
    { label: 'week', seconds: 604800 },
    { label: 'day', seconds: 86400 },
    { label: 'hour', seconds: 3600 },
    { label: 'minute', seconds: 60 },
    { label: 'second', seconds: 1 },
  ];
  
  for (const interval of intervals) {
    const count = Math.floor(diffInSeconds / interval.seconds);
    if (count >= 1) {
      return `${count} ${interval.label}${count > 1 ? 's' : ''} ago`;
    }
  }
  
  return 'just now';
}

/**
 * Alias for formatRelativeTime for backward compatibility
 */
export const formatTimeAgo = formatRelativeTime;

/**
 * Capitalize first letter of a string
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Convert snake_case to Title Case
 */
export function snakeToTitle(str: string): string {
  return str
    .split('_')
    .map(word => capitalize(word))
    .join(' ');
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Generate initials from a name
 */
export function getInitials(name: string): string {
  const words = name.split(' ');
  if (words.length === 1) {
    // For single words, take first two characters
    return name.slice(0, 2).toUpperCase();
  }
  return words
    .map(word => word.charAt(0))
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Generate a random ID
 */
export function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Deep clone an object
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as unknown as T;
  if (typeof obj === 'object') {
    const clonedObj = {} as T;
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
  return obj;
}

/**
 * Check if an object is empty
 */
export function isEmpty(obj: any): boolean {
  if (obj == null) return true;
  if (Array.isArray(obj) || typeof obj === 'string') return obj.length === 0;
  if (typeof obj === 'object') return Object.keys(obj).length === 0;
  return false;
}

/**
 * Sleep function for async operations
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Format file size in human readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Get status color for different states
 */
export function getStatusColor(status: string): string {
  const statusColors: Record<string, string> = {
    // Purchase Order statuses
    draft: 'neutral',
    pending: 'warning',
    confirmed: 'primary',
    shipped: 'primary',
    delivered: 'success',
    cancelled: 'error',
    
    // General statuses
    active: 'success',
    inactive: 'neutral',
    suspended: 'warning',
    terminated: 'error',
    
    // Health statuses
    healthy: 'success',
    degraded: 'warning',
    unhealthy: 'error',
    unknown: 'neutral',
  };
  
  return statusColors[status.toLowerCase()] || 'neutral';
}





/**
 * Format quantity with unit
 */
export function formatQuantity(quantity: number, unit: string): string {
  return `${formatNumber(quantity)} ${unit}`;
}

/**
 * Parse error message from API response with enhanced authentication error handling
 */
export function parseErrorMessage(error: any): string {
  if (typeof error === 'string') return error;
  
  // Handle HTTP status codes
  if (error?.response?.status) {
    const status = error.response.status;
    const data = error.response.data;
    
    switch (status) {
      case 401:
        if (data?.detail?.includes('password') || data?.detail?.includes('credentials')) {
          return 'Invalid email or password. Please check your credentials and try again.';
        }
        return 'Authentication failed. Please check your credentials.';
      
      case 403:
        return 'Access denied. You do not have permission to perform this action.';
      
      case 404:
        return 'The requested resource was not found.';
      
      case 422:
        if (data?.validation_errors?.length > 0) {
          const firstError = data.validation_errors[0];
          return `Validation error: ${firstError.message}`;
        }
        return 'Invalid request data. Please check your input.';
      
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      
      case 500:
        return 'Server error. Please try again later or contact support.';
      
      case 503:
        return 'Service temporarily unavailable. Please try again later.';
      
      default:
        break;
    }
  }
  
  // Handle different error message formats
  if (error?.error?.message) return error.error.message;
  if (error?.message) return error.message;
  if (error?.detail) {
    // Handle specific authentication error messages
    const detail = error.detail;
    if (detail.includes('Incorrect email or password')) {
      return 'Invalid email or password. Please check your credentials and try again.';
    }
    if (detail.includes('User not found')) {
      return 'No account found with this email address.';
    }
    if (detail.includes('Inactive user')) {
      return 'Your account has been deactivated. Please contact support.';
    }
    return detail;
  }
  
  // Handle network errors
  if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network Error')) {
    return 'Network error. Please check your internet connection and try again.';
  }
  
  return 'An unexpected error occurred. Please try again or contact support.';
}

/**
 * Check if user has permission for an action
 */
export function hasPermission(userRole: string, requiredRole: string): boolean {
  const roleHierarchy: Record<string, number> = {
    viewer: 1,
    buyer: 2,
    seller: 2,
    admin: 3,
  };

  const userLevel = roleHierarchy[userRole] || 0;
  const requiredLevel = roleHierarchy[requiredRole] || 0;

  return userLevel >= requiredLevel;
}

/**
 * Generate avatar URL or return initials
 */
export function getAvatarUrl(name: string, email?: string): string {
  // For now, return initials. In the future, could integrate with Gravatar or similar
  return getInitials(name);
}

/**
 * Local storage helpers with error handling
 */
export const storage = {
  get: (key: string): any => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  },
  
  set: (key: string, value: any): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Silently fail if localStorage is not available
    }
  },
  
  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch {
      // Silently fail if localStorage is not available
    }
  },
  
  clear: (): void => {
    try {
      localStorage.clear();
    } catch {
      // Silently fail if localStorage is not available
    }
  },
};
