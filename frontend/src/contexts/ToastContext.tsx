/**
 * Toast Context for managing notifications
 */
import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import Toast, { ToastProps, ToastType } from '../components/ui/Toast';

interface ToastContextType {
  showToast: (toast: Omit<ToastProps, 'id' | 'onClose'>) => void;
  showSuccess: (title: string, message?: string) => void;
  showError: (title: string, message?: string) => void;
  showWarning: (title: string, message?: string) => void;
  showInfo: (title: string, message?: string) => void;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast(): ToastContextType {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

interface ToastProviderProps {
  children: ReactNode;
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastProps[]>([]);
  const [recentToasts, setRecentToasts] = useState<Map<string, number>>(new Map());

  const removeToast = useCallback((id: string) => {
    console.log('Removing toast:', id); // Debug log
    setToasts(prev => {
      const filtered = prev.filter(toast => toast.id !== id);
      console.log('Toasts after removal:', filtered.length); // Debug log
      return filtered;
    });
  }, []);

  const showToast = useCallback((toast: Omit<ToastProps, 'id' | 'onClose'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    console.log('Adding toast:', id, toast.title); // Debug log
    
    // Create a unique key for this toast type
    const toastKey = `${toast.type}-${toast.title}-${toast.message || ''}`;
    const now = Date.now();
    
    // Check for recent duplicate toasts (within 5 seconds)
    setRecentToasts(prev => {
      const recentTime = prev.get(toastKey);
      if (recentTime && (now - recentTime) < 5000) {
        console.log('Recent duplicate toast prevented:', toast.title);
        return prev; // Don't update recent toasts
      }
      
      // Update recent toasts map
      const updated = new Map(prev);
      updated.set(toastKey, now);
      return updated;
    });
    
    // Check for duplicate toasts (same title and message)
    setToasts(prev => {
      const isDuplicate = prev.some(existingToast => 
        existingToast.title === toast.title && 
        existingToast.message === toast.message &&
        existingToast.type === toast.type
      );
      
      if (isDuplicate) {
        console.log('Duplicate toast prevented:', toast.title);
        return prev; // Don't add duplicate
      }
      
      const newToast: ToastProps = {
        ...toast,
        id,
        onClose: removeToast
      };
      
      const updated = [...prev, newToast];
      console.log('Total toasts after adding:', updated.length); // Debug log
      return updated;
    });
  }, [removeToast]);

  const showSuccess = useCallback((title: string, message?: string) => {
    showToast({ type: 'success', title, message });
  }, [showToast]);

  const showError = useCallback((title: string, message?: string) => {
    showToast({ type: 'error', title, message, duration: 7000 }); // Longer duration for errors
  }, [showToast]);

  const showWarning = useCallback((title: string, message?: string) => {
    showToast({ type: 'warning', title, message });
  }, [showToast]);

  const showInfo = useCallback((title: string, message?: string) => {
    showToast({ type: 'info', title, message });
  }, [showToast]);

  const clearAll = useCallback(() => {
    setToasts([]);
  }, []);

  const value: ToastContextType = {
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    removeToast,
    clearAll
  };

  // Create toast portal content
  const toastContent = (
    <div 
      className="fixed top-4 right-4 z-[9999] space-y-2 pointer-events-none"
      style={{
        position: 'fixed',
        top: '1rem',
        right: '1rem',
        zIndex: 9999,
        maxWidth: '400px',
        width: 'auto',
        pointerEvents: 'none'
      }}
    >
      {toasts.map(toast => (
        <div key={toast.id} style={{ pointerEvents: 'auto' }}>
          <Toast {...toast} />
        </div>
      ))}
    </div>
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      
      {/* Render toasts in a portal to avoid layout constraints */}
      {typeof document !== 'undefined' && createPortal(toastContent, document.body)}
    </ToastContext.Provider>
  );
}

export default ToastContext;