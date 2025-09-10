/**
 * Unit tests for utility functions
 */
import {
  cn,
  formatCurrency,
  formatNumber,
  formatDate,
  formatRelativeTime,
  capitalize,
  snakeToTitle,
  truncate,
  getInitials,
  isValidEmail,
  generateId,
  deepClone,
  isEmpty,
  formatFileSize,
  getStatusColor,
  formatTransparency,
  getTransparencyColor,
  formatQuantity,
  parseErrorMessage,
  hasPermission,
  getAvatarUrl,
  storage,
} from '../utils';

describe('Utility Functions', () => {
  describe('cn', () => {
    it('combines class names correctly', () => {
      expect(cn('class1', 'class2')).toBe('class1 class2');
      expect(cn('class1', undefined, 'class2')).toBe('class1 class2');
      expect(cn('class1', false && 'class2', 'class3')).toBe('class1 class3');
    });
  });

  describe('formatCurrency', () => {
    it('formats currency correctly', () => {
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
      expect(formatCurrency(1000, 'EUR')).toBe('€1,000.00');
    });
  });

  describe('formatNumber', () => {
    it('formats numbers correctly', () => {
      expect(formatNumber(1234.56)).toBe('1,234.56');
      expect(formatNumber(1000, { maximumFractionDigits: 0 })).toBe('1,000');
    });
  });

  describe('formatDate', () => {
    it('formats dates correctly', () => {
      const date = new Date('2024-01-15T10:30:00Z');
      const formatted = formatDate(date);
      expect(formatted).toMatch(/Jan 15, 2024/);
    });

    it('formats date strings correctly', () => {
      const formatted = formatDate('2024-01-15T10:30:00Z');
      expect(formatted).toMatch(/Jan 15, 2024/);
    });
  });

  describe('formatRelativeTime', () => {
    it('formats relative time correctly', () => {
      const now = new Date();
      const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
      const twoDaysAgo = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);

      expect(formatRelativeTime(oneHourAgo)).toBe('1 hour ago');
      expect(formatRelativeTime(twoDaysAgo)).toBe('2 days ago');
    });

    it('handles recent times', () => {
      const now = new Date();
      const fiveSecondsAgo = new Date(now.getTime() - 5 * 1000);
      
      expect(formatRelativeTime(fiveSecondsAgo)).toBe('5 seconds ago');
    });
  });

  describe('capitalize', () => {
    it('capitalizes first letter', () => {
      expect(capitalize('hello')).toBe('Hello');
      expect(capitalize('WORLD')).toBe('WORLD');
      expect(capitalize('')).toBe('');
    });
  });

  describe('snakeToTitle', () => {
    it('converts snake_case to Title Case', () => {
      expect(snakeToTitle('hello_world')).toBe('Hello World');
      expect(snakeToTitle('user_profile_settings')).toBe('User Profile Settings');
    });
  });

  describe('truncate', () => {
    it('truncates text correctly', () => {
      expect(truncate('Hello World', 5)).toBe('Hello...');
      expect(truncate('Short', 10)).toBe('Short');
    });
  });

  describe('getInitials', () => {
    it('gets initials from name', () => {
      expect(getInitials('John Doe')).toBe('JD');
      expect(getInitials('Jane Mary Smith')).toBe('JM');
      expect(getInitials('SingleName')).toBe('SI');
    });
  });

  describe('isValidEmail', () => {
    it('validates email addresses', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user.name+tag@domain.co.uk')).toBe(true);
      expect(isValidEmail('invalid-email')).toBe(false);
      expect(isValidEmail('test@')).toBe(false);
      expect(isValidEmail('@example.com')).toBe(false);
    });
  });

  describe('generateId', () => {
    it('generates unique IDs', () => {
      const id1 = generateId();
      const id2 = generateId();
      
      expect(id1).toBeTruthy();
      expect(id2).toBeTruthy();
      expect(id1).not.toBe(id2);
      expect(id1.length).toBe(9);
    });
  });

  describe('deepClone', () => {
    it('deep clones objects', () => {
      const original = { a: 1, b: { c: 2 } };
      const cloned = deepClone(original);
      
      expect(cloned).toEqual(original);
      expect(cloned).not.toBe(original);
      expect(cloned.b).not.toBe(original.b);
    });

    it('handles arrays', () => {
      const original = [1, { a: 2 }, [3, 4]];
      const cloned = deepClone(original);
      
      expect(cloned).toEqual(original);
      expect(cloned).not.toBe(original);
      expect(cloned[1]).not.toBe(original[1]);
    });

    it('handles dates', () => {
      const date = new Date('2024-01-15');
      const cloned = deepClone(date);
      
      expect(cloned).toEqual(date);
      expect(cloned).not.toBe(date);
    });
  });

  describe('isEmpty', () => {
    it('checks if values are empty', () => {
      expect(isEmpty(null)).toBe(true);
      expect(isEmpty(undefined)).toBe(true);
      expect(isEmpty('')).toBe(true);
      expect(isEmpty([])).toBe(true);
      expect(isEmpty({})).toBe(true);
      
      expect(isEmpty('hello')).toBe(false);
      expect(isEmpty([1, 2, 3])).toBe(false);
      expect(isEmpty({ a: 1 })).toBe(false);
      expect(isEmpty(0)).toBe(false);
    });
  });

  describe('formatFileSize', () => {
    it('formats file sizes correctly', () => {
      expect(formatFileSize(0)).toBe('0 Bytes');
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(1048576)).toBe('1 MB');
      expect(formatFileSize(1073741824)).toBe('1 GB');
    });
  });

  describe('getStatusColor', () => {
    it('returns correct colors for statuses', () => {
      expect(getStatusColor('pending')).toBe('warning');
      expect(getStatusColor('confirmed')).toBe('primary');
      expect(getStatusColor('delivered')).toBe('success');
      expect(getStatusColor('cancelled')).toBe('error');
      expect(getStatusColor('unknown_status')).toBe('neutral');
    });
  });

  describe('formatTransparency', () => {
    it('formats transparency values', () => {
      expect(formatTransparency(75.5)).toBe('76%');
      expect(formatTransparency(null)).toBe('N/A');
      expect(formatTransparency(undefined)).toBe('N/A');
    });
  });

  describe('getTransparencyColor', () => {
    it('returns correct colors for transparency scores', () => {
      expect(getTransparencyColor(85)).toBe('success');
      expect(getTransparencyColor(65)).toBe('warning');
      expect(getTransparencyColor(45)).toBe('error');
      expect(getTransparencyColor(25)).toBe('error');
      expect(getTransparencyColor(null)).toBe('neutral');
    });
  });

  describe('formatQuantity', () => {
    it('formats quantities with units', () => {
      expect(formatQuantity(1000, 'KG')).toBe('1,000 KG');
      expect(formatQuantity(500.5, 'LB')).toBe('500.5 LB');
    });
  });

  describe('parseErrorMessage', () => {
    it('parses error messages from different formats', () => {
      expect(parseErrorMessage('Simple error')).toBe('Simple error');
      expect(parseErrorMessage({ error: { message: 'API error' } })).toBe('API error');
      expect(parseErrorMessage({ message: 'Direct message' })).toBe('Direct message');
      expect(parseErrorMessage({ detail: 'Detail message' })).toBe('Detail message');
      expect(parseErrorMessage({})).toBe('An unexpected error occurred');
    });
  });

  describe('hasPermission', () => {
    it('checks role permissions correctly', () => {
      expect(hasPermission('admin', 'viewer')).toBe(true);
      expect(hasPermission('buyer', 'viewer')).toBe(true);
      expect(hasPermission('viewer', 'admin')).toBe(false);
      expect(hasPermission('buyer', 'seller')).toBe(true); // Same level
    });
  });

  describe('getAvatarUrl', () => {
    it('returns initials for now', () => {
      expect(getAvatarUrl('John Doe')).toBe('JD');
      expect(getAvatarUrl('Jane Smith', 'jane@example.com')).toBe('JS');
    });
  });

  describe('storage', () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('gets items from localStorage', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('{"test": "value"}');
      
      const result = storage.get('test-key');
      
      expect(localStorage.getItem).toHaveBeenCalledWith('test-key');
      expect(result).toEqual({ test: 'value' });
    });

    it('sets items in localStorage', () => {
      storage.set('test-key', { test: 'value' });
      
      expect(localStorage.setItem).toHaveBeenCalledWith('test-key', '{"test":"value"}');
    });

    it('removes items from localStorage', () => {
      storage.remove('test-key');
      
      expect(localStorage.removeItem).toHaveBeenCalledWith('test-key');
    });

    it('clears localStorage', () => {
      storage.clear();
      
      expect(localStorage.clear).toHaveBeenCalled();
    });

    it('handles errors gracefully', () => {
      (localStorage.getItem as jest.Mock).mockImplementation(() => {
        throw new Error('Storage error');
      });
      
      expect(storage.get('test-key')).toBe(null);
    });
  });
});
