/**
 * Company Onboarding Wizard Component
 * Role-specific guidance for company setup
 */
import React, { useState, useEffect } from 'react';
import { 
  BuildingOfficeIcon,
  UserIcon,
  MapPinIcon,
  DocumentCheckIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { CompanyOnboardingData, UserOnboardingData, OnboardingProgress } from '../../types/onboarding';
import { onboardingApi } from '../../lib/onboardingApi';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Textarea from '../ui/Textarea';
import Badge from '../ui/Badge';
import { cn } from '../../lib/utils';

interface CompanyOnboardingWizardProps {
  invitationToken?: string;
  companyType?: 'plantation_grower' | 'smallholder_cooperative' | 'mill_processor' | 'refinery_crusher' | 'trader_aggregator' | 'oleochemical_producer' | 'manufacturer';
  onComplete?: (result: { company_id: string; user_id: string; access_token: string }) => void;
  className?: string;
}

const CompanyOnboardingWizard: React.FC<CompanyOnboardingWizardProps> = ({
  invitationToken,
  companyType,
  onComplete,
  className,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [companyData, setCompanyData] = useState<CompanyOnboardingData>({
    id: undefined,
    company_name: '',
    company_type: companyType || 'plantation_grower',
    email: '',
    phone: '',
    website: '',
    description: '',
    address: {
      street: '',
      city: '',
      state: '',
      postal_code: '',
      country: 'United States',
    },
    business_registration_number: '',
    tax_id: '',
    industry_sector: '',
    annual_revenue: '',
    employee_count: '',
    certifications: [],
    compliance_standards: [],
    primary_contact: {
      full_name: '',
      email: '',
      phone: '',
      title: '',
    },
  });

  const [userData, setUserData] = useState<UserOnboardingData>({
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
    title: '',
    phone: '',
    role: 'admin',
    department: '',
  });

  // Onboarding steps configuration
  const steps = [
    {
      id: 'welcome',
      title: 'Welcome',
      description: 'Get started with your supply chain transparency journey',
      icon: CheckCircleIcon,
      estimatedTime: 1,
    },
    {
      id: 'company-basic',
      title: 'Company Information',
      description: 'Basic company details and contact information',
      icon: BuildingOfficeIcon,
      estimatedTime: 5,
    },
    {
      id: 'company-address',
      title: 'Address & Location',
      description: 'Company address and geographic information',
      icon: MapPinIcon,
      estimatedTime: 3,
    },
    {
      id: 'business-details',
      title: 'Business Details',
      description: 'Registration, tax, and industry information',
      icon: DocumentCheckIcon,
      estimatedTime: 4,
    },
    {
      id: 'certifications',
      title: 'Certifications',
      description: 'Sustainability and compliance certifications',
      icon: ShieldCheckIcon,
      estimatedTime: 3,
    },
    {
      id: 'user-account',
      title: 'User Account',
      description: 'Create your admin user account',
      icon: UserIcon,
      estimatedTime: 3,
    },
    {
      id: 'review',
      title: 'Review & Complete',
      description: 'Review your information and complete setup',
      icon: CheckCircleIcon,
      estimatedTime: 2,
    },
  ];

  // Get role-specific guidance
  const getRoleGuidance = () => {
    const guidance = {
      plantation_grower: {
        title: 'Plantation / Grower Setup',
        description: 'As a plantation or grower, you\'ll be providing raw palm fruit and origin data to the supply chain.',
        tips: [
          'Document your farming practices and certifications',
          'Set up location and sustainability data sharing',
          'Configure quality and origin certifications',
        ],
      },
      smallholder_cooperative: {
        title: 'Smallholder / Cooperative Setup',
        description: 'As a smallholder cooperative, you\'ll be aggregating production from multiple small-scale farmers.',
        tips: [
          'Document member farmer practices and locations',
          'Set up aggregated production tracking',
          'Configure cooperative certifications and standards',
        ],
      },
      mill_processor: {
        title: 'Mill / Processor Setup',
        description: 'As a mill or processor, you\'ll be extracting crude palm oil from fresh fruit bunches.',
        tips: [
          'Document your processing capabilities and certifications',
          'Set up input material tracking for transparency',
          'Configure quality metrics and processing data sharing',
        ],
      },
      refinery_crusher: {
        title: 'Refinery / Crusher Setup',
        description: 'As a refinery or crusher, you\'ll be refining crude palm oil into derivatives for manufacturers.',
        tips: [
          'Document refining processes and quality standards',
          'Set up input-output tracking for transparency',
          'Configure derivative product specifications',
        ],
      },
      trader_aggregator: {
        title: 'Trader / Aggregator Setup',
        description: 'As a trader or aggregator, you\'ll be buying, consolidating, and selling commodities across markets.',
        tips: [
          'Focus on building relationships with sustainable suppliers',
          'Set up transparency requirements for your supply chain',
          'Configure data sharing to track product origins',
        ],
      },
      oleochemical_producer: {
        title: 'Oleochemical Producer Setup',
        description: 'As an oleochemical producer, you\'ll be converting palm oil derivatives into specialized ingredients.',
        tips: [
          'Document specialized production capabilities',
          'Set up ingredient traceability systems',
          'Configure end-product specifications and certifications',
        ],
      },
      manufacturer: {
        title: 'Manufacturer Setup',
        description: 'As a consumer goods manufacturer, you\'ll be producing finished personal care and adhesive products using palm oil derivatives.',
        tips: [
          'Document finished product formulations and specifications',
          'Set up ingredient sourcing and traceability systems',
          'Configure consumer product certifications and compliance',
        ],
      },
    };

    return guidance[companyData.company_type];
  };

  // Handle field changes
  const handleCompanyFieldChange = (field: string, value: any) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setCompanyData(prev => ({
        ...prev,
        [parent]: {
          ...(prev[parent as keyof CompanyOnboardingData] as object),
          [child]: value,
        },
      }));
    } else {
      setCompanyData(prev => ({ ...prev, [field]: value }));
    }
    
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleUserFieldChange = (field: string, value: string) => {
    setUserData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  // Validate current step
  const validateStep = (stepIndex: number): boolean => {
    const newErrors: Record<string, string> = {};
    const step = steps[stepIndex];

    switch (step.id) {
      case 'company-basic':
        if (!companyData.company_name) newErrors.company_name = 'Company name is required';
        if (!companyData.email) newErrors.email = 'Email is required';
        if (!companyData.company_type) newErrors.company_type = 'Company type is required';
        break;

      case 'company-address':
        if (!companyData.address.street) newErrors['address.street'] = 'Street address is required';
        if (!companyData.address.city) newErrors['address.city'] = 'City is required';
        if (!companyData.address.country) newErrors['address.country'] = 'Country is required';
        break;

      case 'user-account':
        if (!userData.full_name) newErrors.full_name = 'Full name is required';
        if (!userData.email) newErrors.user_email = 'Email is required';
        if (!userData.password) newErrors.password = 'Password is required';
        if (userData.password !== userData.confirm_password) {
          newErrors.confirm_password = 'Passwords do not match';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle step navigation
  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, steps.length - 1));
    }
  };

  const handleBack = () => {
    setCurrentStep(prev => Math.max(prev - 1, 0));
  };

  // Handle form submission
  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setIsSubmitting(true);
    try {
      const updateData = {
        id: companyData.id || 'temp-id',
        company_name: companyData.company_name,
        company_type: companyData.company_type,
        address: companyData.address,
        phone: companyData.phone,
        website: companyData.website,
        user_data: userData,
        status: 'completed' as const
      };
      const result = await onboardingApi.updateCompanyOnboarding(updateData.id, updateData);
      if (onComplete) {
        // Transform result to match expected callback type
        onComplete({
          company_id: result.id || updateData.id,
          user_id: userData.email, // Use user email as temp user ID
          access_token: 'temp-access-token' // Placeholder token
        });
      }
    } catch (error) {
      console.error('Onboarding failed:', error);
      setErrors({ submit: 'Failed to complete onboarding. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Render step progress
  const renderStepProgress = () => (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-neutral-900">
          Step {currentStep + 1} of {steps.length}
        </h2>
        <div className="flex items-center space-x-2 text-sm text-neutral-600">
          <ClockIcon className="h-4 w-4" />
          <span>{steps[currentStep].estimatedTime} min</span>
        </div>
      </div>
      
      <div className="w-full bg-neutral-200 rounded-full h-2 mb-4">
        <div 
          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
        />
      </div>

      <div className="flex items-center space-x-2">
        {steps[currentStep].icon && React.createElement(steps[currentStep].icon, {
          className: "h-5 w-5 text-primary-600"
        })}
        <div>
          <h3 className="font-medium text-neutral-900">{steps[currentStep].title}</h3>
          <p className="text-sm text-neutral-600">{steps[currentStep].description}</p>
        </div>
      </div>
    </div>
  );

  // Render welcome step
  const renderWelcomeStep = () => {
    const guidance = getRoleGuidance();
    
    return (
      <div className="text-center space-y-6">
        <div className="mx-auto h-16 w-16 bg-primary-600 rounded-xl flex items-center justify-center">
          <BuildingOfficeIcon className="h-8 w-8 text-white" />
        </div>
        
        <div>
          <h2 className="text-2xl font-bold text-neutral-900 mb-2">
            {guidance?.title}
          </h2>
          <p className="text-neutral-600 max-w-md mx-auto">
            {guidance?.description}
          </p>
        </div>

        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4 text-left">
          <h4 className="font-medium text-primary-900 mb-3">Getting Started Tips:</h4>
          <ul className="space-y-2">
            {guidance?.tips.map((tip, index) => (
              <li key={index} className="flex items-start space-x-2 text-sm text-primary-800">
                <CheckCircleIcon className="h-4 w-4 text-primary-600 mt-0.5 flex-shrink-0" />
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="text-sm text-neutral-600">
          This setup will take approximately {steps.reduce((sum, step) => sum + step.estimatedTime, 0)} minutes to complete.
        </div>
      </div>
    );
  };

  // Render company basic info step
  const renderCompanyBasicStep = () => (
    <div className="space-y-4">
      <div>
        <Input
          label="Company Name"
          value={companyData.company_name}
          onChange={(e) => handleCompanyFieldChange('company_name', e.target.value)}
          errorMessage={errors.company_name}
          placeholder="Your Company Name"
          required
        />
      </div>

      <div>
        <Select
          label="Company Type"
          value={companyData.company_type}
          onChange={(e) => handleCompanyFieldChange('company_type', e.target.value)}
          errorMessage={errors.company_type}
          required
          disabled={!!companyType}
          options={[
            { label: 'Plantation / Grower (Farms & Estates)', value: 'plantation_grower' },
            { label: 'Smallholder / Cooperative (Small-scale Farmers)', value: 'smallholder_cooperative' },
            { label: 'Mill / Processor (Oil Extraction)', value: 'mill_processor' },
            { label: 'Refinery / Crusher (Oil Refining)', value: 'refinery_crusher' },
            { label: 'Trader / Aggregator (Commodity Trading)', value: 'trader_aggregator' },
            { label: 'Oleochemical Producer (Specialized Manufacturing)', value: 'oleochemical_producer' },
            { label: 'Manufacturer (Consumer Goods)', value: 'manufacturer' }
          ]}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Company Email"
          type="email"
          value={companyData.email}
          onChange={(e) => handleCompanyFieldChange('email', e.target.value)}
          errorMessage={errors.email}
          placeholder="contact@company.com"
          required
        />

        <Input
          label="Phone Number"
          type="tel"
          value={companyData.phone || ''}
          onChange={(e) => handleCompanyFieldChange('phone', e.target.value)}
          placeholder="+1 (555) 123-4567"
        />
      </div>

      <div>
        <Input
          label="Website"
          type="url"
          value={companyData.website || ''}
          onChange={(e) => handleCompanyFieldChange('website', e.target.value)}
          placeholder="https://www.company.com"
        />
      </div>

      <div>
        <Textarea
          label="Company Description"
          value={companyData.description || ''}
          onChange={(e) => handleCompanyFieldChange('description', e.target.value)}
          placeholder="Brief description of your company and what you do..."
          rows={3}
        />
      </div>
    </div>
  );

  // Render address step
  const renderAddressStep = () => (
    <div className="space-y-4">
      <div>
        <Input
          label="Street Address"
          value={companyData.address.street}
          onChange={(e) => handleCompanyFieldChange('address.street', e.target.value)}
          errorMessage={errors['address.street']}
          placeholder="123 Main Street"
          required
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="City"
          value={companyData.address.city}
          onChange={(e) => handleCompanyFieldChange('address.city', e.target.value)}
          errorMessage={errors['address.city']}
          placeholder="City"
          required
        />

        <Input
          label="State/Province"
          value={companyData.address.state}
          onChange={(e) => handleCompanyFieldChange('address.state', e.target.value)}
          placeholder="State"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Postal Code"
          value={companyData.address.postal_code}
          onChange={(e) => handleCompanyFieldChange('address.postal_code', e.target.value)}
          placeholder="12345"
        />

        <Select
          label="Country"
          value={companyData.address.country}
          onChange={(e) => handleCompanyFieldChange('address.country', e.target.value)}
          errorMessage={errors['address.country']}
          required
          options={[
            { label: 'United States', value: 'United States' },
            { label: 'Canada', value: 'Canada' },
            { label: 'Mexico', value: 'Mexico' },
            { label: 'United Kingdom', value: 'United Kingdom' },
            { label: 'Germany', value: 'Germany' },
            { label: 'France', value: 'France' },
            { label: 'Other', value: 'Other' }
          ]}
        />
      </div>
    </div>
  );

  return (
    <Card className={className}>
      <CardHeader 
        title="Company Onboarding"
        subtitle="Set up your company profile and user account"
      />
      
      <CardBody>
        {renderStepProgress()}

        <div className="mb-8">
          {currentStep === 0 && renderWelcomeStep()}
          {currentStep === 1 && renderCompanyBasicStep()}
          {currentStep === 2 && renderAddressStep()}
          {/* Additional steps would be implemented here */}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={currentStep === 0}
          >
            Back
          </Button>

          <div className="flex space-x-3">
            {currentStep === steps.length - 1 ? (
              <Button
                variant="primary"
                onClick={handleSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Completing...' : 'Complete Setup'}
              </Button>
            ) : (
              <Button
                variant="primary"
                onClick={handleNext}
              >
                Next
              </Button>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default CompanyOnboardingWizard;
