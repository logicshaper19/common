/**
 * Login Page Component
 */
import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import { Card, CardBody } from '../components/ui/Card';
import { isValidEmail } from '../lib/utils';

const Login: React.FC = () => {
  const { login, isAuthenticated, isLoading, error, clearError } = useAuth();
  const location = useLocation();
  
  // Form state
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Clear errors when component mounts or form data changes
  useEffect(() => {
    clearError();
    setFormErrors({});
  }, [formData, clearError]);

  // Redirect if already authenticated
  if (isAuthenticated) {
    const from = (location.state as any)?.from?.pathname || '/dashboard';
    return <Navigate to={from} replace />;
  }

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  // Validate form
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!isValidEmail(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      await login(formData);
    } catch (error) {
      // Error is handled by the auth context
      console.error('Login failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Toggle password visibility
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto mb-6">
            <span className="text-4xl font-bold text-black lowercase">common</span>
          </div>
          <h2 className="text-3xl font-bold text-neutral-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-sm text-neutral-600">
            Supply Chain Transparency Platform
          </p>
        </div>

        {/* Login form */}
        <Card>
          <CardBody>
            <form className="space-y-6" onSubmit={handleSubmit}>
              {/* Enhanced error message with guidance */}
              {error && (
                <div className="bg-error-50 border border-error-200 rounded-lg p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-error-400"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-error-800 mb-2">
                        {error.includes('password') || error.includes('credentials') || error.includes('401') 
                          ? 'Invalid email or password' 
                          : error}
                      </p>
                      {(error.includes('password') || error.includes('credentials') || error.includes('401')) && (
                        <div className="text-xs text-error-700 space-y-1">
                          <p className="font-medium">💡 Login Help:</p>
                          <p>• Double-check your email address and password</p>
                          <p>• Make sure Caps Lock is not enabled</p>
                          <p>• Ensure your account is active and not locked</p>
                          <p className="mt-2 text-error-600">
                            If you're still having trouble, contact your system administrator.
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Email field */}
              <Input
                label="Email address"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                errorMessage={formErrors.email}
                placeholder="Enter your email"
                isRequired
                autoComplete="email"
                leftIcon={
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"
                    />
                  </svg>
                }
              />

              {/* Password field */}
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                errorMessage={formErrors.password}
                placeholder="Enter your password"
                isRequired
                autoComplete="current-password"
                leftIcon={
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                }
                rightIcon={
                  <button
                    type="button"
                    onClick={togglePasswordVisibility}
                    className="text-neutral-400 hover:text-neutral-600 focus:outline-none"
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="h-4 w-4" />
                    ) : (
                      <EyeIcon className="h-4 w-4" />
                    )}
                  </button>
                }
              />

              {/* Submit button */}
              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                isLoading={isSubmitting || isLoading}
                disabled={isSubmitting || isLoading}
              >
                {isSubmitting || isLoading ? 'Signing in...' : 'Sign in'}
              </Button>
            </form>

            {/* Help section */}
            <div className="mt-6 pt-6 border-t border-neutral-200">
              <div className="text-center">
                <p className="text-sm text-neutral-600">
                  Need help accessing your account?
                </p>
                <p className="text-xs text-neutral-500 mt-1">
                  Contact your system administrator or check the documentation.
                </p>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-neutral-500">
            © 2024 Common Supply Chain Platform. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
