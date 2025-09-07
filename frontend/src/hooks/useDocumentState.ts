/**
 * Custom hook for managing document state with reducer pattern
 * Consolidates complex document state management logic
 */
import { useReducer, useCallback, useEffect } from 'react';
import { Document } from '../api/documents';
import { DocumentRequirement } from '../components/documents/DocumentUploadProgress';

// Document state interface
interface DocumentState {
  uploadedDocuments: Document[];
  requirements: DocumentRequirement[];
  allRequiredUploaded: boolean;
  isLoading: boolean;
  error: string | null;
  uploadProgress: Record<string, number>;
  validationStatus: Record<string, 'valid' | 'invalid' | 'pending'>;
}

// Action types
type DocumentAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_REQUIREMENTS'; payload: DocumentRequirement[] }
  | { type: 'DOCUMENT_UPLOADED'; payload: Document }
  | { type: 'DOCUMENT_REMOVED'; payload: string } // document ID
  | { type: 'UPDATE_UPLOAD_PROGRESS'; payload: { documentType: string; progress: number } }
  | { type: 'UPDATE_VALIDATION_STATUS'; payload: { documentId: string; status: 'valid' | 'invalid' | 'pending' } }
  | { type: 'BATCH_UPDATE_DOCUMENTS'; payload: Document[] }
  | { type: 'BATCH_UPDATE_PROGRESS'; payload: Record<string, number> }
  | { type: 'BATCH_UPDATE_VALIDATION'; payload: Record<string, 'valid' | 'invalid' | 'pending'> }
  | { type: 'RESET_STATE' }
  | { type: 'UPDATE_ALL_REQUIRED_STATUS'; payload: boolean };

// Initial state
const initialState: DocumentState = {
  uploadedDocuments: [],
  requirements: [],
  allRequiredUploaded: false,
  isLoading: false,
  error: null,
  uploadProgress: {},
  validationStatus: {}
};

// Reducer function
function documentReducer(state: DocumentState, action: DocumentAction): DocumentState {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false
      };

    case 'SET_REQUIREMENTS':
      return {
        ...state,
        requirements: action.payload,
        error: null
      };

    case 'DOCUMENT_UPLOADED': {
      const newDocument = action.payload;
      
      // Remove any existing document of the same type
      const filteredDocuments = state.uploadedDocuments.filter(
        doc => doc.document_type !== newDocument.document_type
      );
      
      const updatedDocuments = [...filteredDocuments, newDocument];
      
      // Calculate if all required documents are uploaded
      const allRequiredUploaded = calculateAllRequiredUploaded(state.requirements, updatedDocuments);
      
      return {
        ...state,
        uploadedDocuments: updatedDocuments,
        allRequiredUploaded,
        uploadProgress: {
          ...state.uploadProgress,
          [newDocument.document_type]: 100
        },
        validationStatus: {
          ...state.validationStatus,
          [newDocument.id]: 'valid'
        },
        error: null
      };
    }

    case 'DOCUMENT_REMOVED': {
      const documentId = action.payload;
      const updatedDocuments = state.uploadedDocuments.filter(doc => doc.id !== documentId);
      const allRequiredUploaded = calculateAllRequiredUploaded(state.requirements, updatedDocuments);
      
      // Remove from validation status
      const { [documentId]: removed, ...remainingValidationStatus } = state.validationStatus;
      
      return {
        ...state,
        uploadedDocuments: updatedDocuments,
        allRequiredUploaded,
        validationStatus: remainingValidationStatus
      };
    }

    case 'UPDATE_UPLOAD_PROGRESS':
      return {
        ...state,
        uploadProgress: {
          ...state.uploadProgress,
          [action.payload.documentType]: action.payload.progress
        }
      };

    case 'UPDATE_VALIDATION_STATUS':
      return {
        ...state,
        validationStatus: {
          ...state.validationStatus,
          [action.payload.documentId]: action.payload.status
        }
      };

    case 'UPDATE_ALL_REQUIRED_STATUS':
      return {
        ...state,
        allRequiredUploaded: action.payload
      };

    case 'BATCH_UPDATE_DOCUMENTS': {
      const newDocuments = action.payload;
      const allRequiredUploaded = calculateAllRequiredUploaded(state.requirements, newDocuments);

      return {
        ...state,
        uploadedDocuments: newDocuments,
        allRequiredUploaded,
        error: null
      };
    }

    case 'BATCH_UPDATE_PROGRESS':
      return {
        ...state,
        uploadProgress: {
          ...state.uploadProgress,
          ...action.payload
        }
      };

    case 'BATCH_UPDATE_VALIDATION':
      return {
        ...state,
        validationStatus: {
          ...state.validationStatus,
          ...action.payload
        }
      };

    case 'RESET_STATE':
      return initialState;

    default:
      return state;
  }
}

// Helper function to calculate if all required documents are uploaded
function calculateAllRequiredUploaded(
  requirements: DocumentRequirement[],
  uploadedDocuments: Document[]
): boolean {
  const requiredTypes = requirements
    .filter(req => req.required)
    .map(req => req.type);
  
  const uploadedTypes = uploadedDocuments.map(doc => doc.document_type);
  
  return requiredTypes.every(type => uploadedTypes.includes(type));
}

// Custom hook
export function useDocumentState(initialRequirements: DocumentRequirement[] = []) {
  const [state, dispatch] = useReducer(documentReducer, {
    ...initialState,
    requirements: initialRequirements
  });

  // Action creators
  const setLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  }, []);

  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  }, []);

  const setRequirements = useCallback((requirements: DocumentRequirement[]) => {
    dispatch({ type: 'SET_REQUIREMENTS', payload: requirements });
  }, []);

  const addDocument = useCallback((document: Document) => {
    dispatch({ type: 'DOCUMENT_UPLOADED', payload: document });
  }, []);

  const removeDocument = useCallback((documentId: string) => {
    dispatch({ type: 'DOCUMENT_REMOVED', payload: documentId });
  }, []);

  const updateUploadProgress = useCallback((documentType: string, progress: number) => {
    dispatch({ 
      type: 'UPDATE_UPLOAD_PROGRESS', 
      payload: { documentType, progress } 
    });
  }, []);

  const updateValidationStatus = useCallback((documentId: string, status: 'valid' | 'invalid' | 'pending') => {
    dispatch({ 
      type: 'UPDATE_VALIDATION_STATUS', 
      payload: { documentId, status } 
    });
  }, []);

  const updateAllRequiredStatus = useCallback((allRequired: boolean) => {
    dispatch({ type: 'UPDATE_ALL_REQUIRED_STATUS', payload: allRequired });
  }, []);

  const resetState = useCallback(() => {
    dispatch({ type: 'RESET_STATE' });
  }, []);

  // Batch operations for better performance
  const batchUpdateDocuments = useCallback((documents: Document[]) => {
    dispatch({ type: 'BATCH_UPDATE_DOCUMENTS', payload: documents });
  }, []);

  const batchUpdateProgress = useCallback((progressMap: Record<string, number>) => {
    dispatch({ type: 'BATCH_UPDATE_PROGRESS', payload: progressMap });
  }, []);

  const batchUpdateValidation = useCallback((validationMap: Record<string, 'valid' | 'invalid' | 'pending'>) => {
    dispatch({ type: 'BATCH_UPDATE_VALIDATION', payload: validationMap });
  }, []);

  // Derived state
  const getDocumentByType = useCallback((documentType: string): Document | undefined => {
    return state.uploadedDocuments.find(doc => doc.document_type === documentType);
  }, [state.uploadedDocuments]);

  const getUploadProgress = useCallback((documentType: string): number => {
    return state.uploadProgress[documentType] || 0;
  }, [state.uploadProgress]);

  const getValidationStatus = useCallback((documentId: string): 'valid' | 'invalid' | 'pending' => {
    return state.validationStatus[documentId] || 'pending';
  }, [state.validationStatus]);

  const getMissingRequiredDocuments = useCallback((): DocumentRequirement[] => {
    const uploadedTypes = state.uploadedDocuments.map(doc => doc.document_type);
    return state.requirements.filter(req => req.required && !uploadedTypes.includes(req.type));
  }, [state.requirements, state.uploadedDocuments]);

  const getCompletionPercentage = useCallback((): number => {
    if (state.requirements.length === 0) return 0;
    const completed = state.uploadedDocuments.length;
    return Math.round((completed / state.requirements.length) * 100);
  }, [state.requirements.length, state.uploadedDocuments.length]);

  // Update all required status when dependencies change
  useEffect(() => {
    const allRequired = calculateAllRequiredUploaded(state.requirements, state.uploadedDocuments);
    if (allRequired !== state.allRequiredUploaded) {
      updateAllRequiredStatus(allRequired);
    }
  }, [state.requirements, state.uploadedDocuments, state.allRequiredUploaded, updateAllRequiredStatus]);

  return {
    // State
    ...state,
    
    // Actions
    setLoading,
    setError,
    setRequirements,
    addDocument,
    removeDocument,
    updateUploadProgress,
    updateValidationStatus,
    updateAllRequiredStatus,
    resetState,

    // Batch operations
    batchUpdateDocuments,
    batchUpdateProgress,
    batchUpdateValidation,
    
    // Derived state and helpers
    getDocumentByType,
    getUploadProgress,
    getValidationStatus,
    getMissingRequiredDocuments,
    getCompletionPercentage
  };
}
