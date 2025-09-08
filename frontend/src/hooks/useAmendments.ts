import { useState, useCallback } from 'react';
import { 
  purchaseOrderApi, 
  ProposeChangesRequest, 
  ApproveChangesRequest, 
  AmendmentResponse 
} from '../services/purchaseOrderApi';

interface UseAmendmentsReturn {
  proposeChanges: (poId: string, proposal: ProposeChangesRequest) => Promise<AmendmentResponse>;
  approveChanges: (poId: string, approval: ApproveChangesRequest) => Promise<AmendmentResponse>;
  isLoading: boolean;
  error: string | null;
}

export const useAmendments = (): UseAmendmentsReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const proposeChanges = useCallback(async (
    poId: string, 
    proposal: ProposeChangesRequest
  ): Promise<AmendmentResponse> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await purchaseOrderApi.proposeChanges(poId, proposal);
      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to propose changes';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const approveChanges = useCallback(async (
    poId: string, 
    approval: ApproveChangesRequest
  ): Promise<AmendmentResponse> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await purchaseOrderApi.approveChanges(poId, approval);
      return response;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to process amendment decision';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    proposeChanges,
    approveChanges,
    isLoading,
    error
  };
};

export default useAmendments;
