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
        per_page: 1 // We only need the total count, not the actual data
      });

      setTotalCount(response.total);

      // For now, use total count as pending count since status filtering has issues
      // TODO: Fix status filtering in the API
      setPendingCount(response.total);
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
