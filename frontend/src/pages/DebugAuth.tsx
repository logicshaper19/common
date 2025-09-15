import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiClient } from '../lib/api';

const DebugAuth: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const testAuth = async () => {
    try {
      setError(null);
      const response = await apiClient.get('/purchase-orders/debug-auth');
      setDebugInfo(response.data);
    } catch (err: any) {
      setError(err.message || 'Unknown error');
      console.error('Auth test error:', err);
    }
  };

  const testIncomingPOs = async () => {
    try {
      setError(null);
      const response = await apiClient.get('/purchase-orders/incoming-simple');
      setDebugInfo({ incomingPOs: response.data });
    } catch (err: any) {
      setError(err.message || 'Unknown error');
      console.error('Incoming POs test error:', err);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Authentication Debug</h1>
      
      <div className="space-y-4">
        <div className="bg-gray-100 p-4 rounded">
          <h2 className="text-lg font-semibold mb-2">Auth State</h2>
          <p>Is Authenticated: {isAuthenticated ? 'Yes' : 'No'}</p>
          <p>Is Loading: {isLoading ? 'Yes' : 'No'}</p>
          <p>User: {user ? JSON.stringify(user, null, 2) : 'None'}</p>
        </div>

        <div className="bg-gray-100 p-4 rounded">
          <h2 className="text-lg font-semibold mb-2">Token Info</h2>
          <p>Token: {apiClient.getToken() ? 'Present' : 'Missing'}</p>
          <p>Token Value: {apiClient.getToken()?.substring(0, 20)}...</p>
        </div>

        <div className="space-x-4">
          <button
            onClick={testAuth}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Test Auth Endpoint
          </button>
          <button
            onClick={testIncomingPOs}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
          >
            Test Incoming POs
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <strong>Error:</strong> {error}
          </div>
        )}

        {debugInfo && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            <strong>Debug Info:</strong>
            <pre className="mt-2 whitespace-pre-wrap">{JSON.stringify(debugInfo, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default DebugAuth;
