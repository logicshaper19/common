import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { purchaseOrderApi } from '../services/purchaseOrderApi';

export interface UsePurchaseOrderCountReturn {
  totalCount: number;
  pendingCount: number;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export const usePurchaseOrderCount = (): UsePurchaseOrderCountReturn => {
  const { user, isAuthenticated } = useAuth();
  const [totalCount, setTotalCount] = useState(0);
  const [pendingCount, setPendingCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCounts = useCallback(async () => {
    if (!isAuthenticated || !user) {
      setTotalCount(0);
      setPendingCount(0);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Fetch all purchase orders to get total count
      const response = await purchaseOrderApi.getPurchaseOrders({
        page: 1,
        per_page: 100 // Get more orders to properly count pending ones
      });

      setTotalCount(response.total);

      // Count only pending orders (not confirmed, rejected, etc.)
      const purchaseOrders = response.purchase_orders || [];
      const pendingOrders = purchaseOrders.filter(po => 
        po.status && 
        (po.status.toLowerCase() === 'pending' || 
         po.status.toLowerCase() === 'awaiting_acceptance' ||
         po.status.toLowerCase() === 'awaiting_confirmation')
      );
      
      setPendingCount(pendingOrders.length);
    } catch (err) {
      console.error('Error fetching purchase order counts:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch counts');
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user]);

  // Auto-fetch when component mounts or user changes
  useEffect(() => {
    fetchCounts();
  }, [fetchCounts]);

  return {
    totalCount,
    pendingCount,
    loading,
    error,
    refresh: fetchCounts,
  };
};
