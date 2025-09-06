import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

// Mock the API client
jest.mock('./lib/api', () => ({
  apiClient: {
    getCurrentUser: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
    clearToken: jest.fn(),
  },
}));

test('renders app without crashing', () => {
  render(<App />);
  // App should render without throwing errors
  expect(document.body).toBeInTheDocument();
});
