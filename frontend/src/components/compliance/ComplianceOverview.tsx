/**
 * Compliance Overview Component
 * Following the project plan: Display compliance status on PO Detail Page
 */
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';
import { complianceApi } from '../../services/complianceApi';

interface ComplianceCheck {
  check_name: string;
  status: 'pass' | 'fail' | 'warning' | 'pending';
  checked_at?: string;
}

interface RegulationCompliance {
  status: 'pass' | 'fail' | 'warning' | 'pending';
  checks_passed: number;
  total_checks: number;
  checks: ComplianceCheck[];
}

interface ComplianceOverviewData {
  [regulation: string]: RegulationCompliance;
}

interface ComplianceOverviewProps {
  poId: string;
  onGenerateReport?: () => void;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'pass':
      return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
    case 'fail':
      return <XCircleIcon className="h-4 w-4 text-red-600" />;
    case 'warning':
      return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600" />;
    case 'pending':
      return <ClockIcon className="h-4 w-4 text-gray-600" />;
    default:
      return <ClockIcon className="h-4 w-4 text-gray-600" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'pass':
      return 'bg-green-100 text-green-800 border-green-200';
    case 'fail':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'warning':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'pending':
      return 'bg-gray-100 text-gray-800 border-gray-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

export const ComplianceOverview: React.FC<ComplianceOverviewProps> = ({
  poId,
  onGenerateReport
}) => {
  const [complianceData, setComplianceData] = useState<ComplianceOverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  useEffect(() => {
    loadComplianceData();
  }, [poId]);

  const loadComplianceData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await complianceApi.getComplianceOverview(poId);
      setComplianceData(response.compliance_overview);
    } catch (err) {
      console.error('Error loading compliance data:', err);
      setError('Failed to load compliance data');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    try {
      setGeneratingReport(true);
      
      // Download the PDF report
      const blob = await complianceApi.generateComplianceReport(poId);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `compliance_report_${poId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      if (onGenerateReport) {
        onGenerateReport();
      }
    } catch (err) {
      console.error('Error generating report:', err);
      setError('Failed to generate compliance report');
    } finally {
      setGeneratingReport(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader title="Loading Compliance Status" />
        <CardBody>
          <div className="flex items-center justify-center py-8">
            <ClockIcon className="h-6 w-6 text-neutral-400 mr-2 animate-spin" />
            <span className="text-neutral-500">Checking compliance status...</span>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader title="Compliance Status" />
        <CardBody>
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-4 w-4 text-red-600 mr-2" />
              <span className="text-red-800">{error}</span>
            </div>
          </div>
          <Button
            onClick={loadComplianceData}
            variant="outline"
            size="sm"
            className="mt-3"
          >
            Retry
          </Button>
        </CardBody>
      </Card>
    );
  }

  if (!complianceData || Object.keys(complianceData).length === 0) {
    return (
      <Card>
        <CardHeader title="Compliance Status" />
        <CardBody>
          <div className="text-sm text-gray-600">
            No compliance checks have been performed for this purchase order.
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader
        title="Compliance Status"
        action={
          <Button
            onClick={handleGenerateReport}
            disabled={generatingReport}
            size="sm"
            className="flex items-center gap-2"
          >
            {generatingReport ? (
              <ClockIcon className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            )}
            Generate Report
          </Button>
        }
      />
      <CardBody className="space-y-4">
        {Object.entries(complianceData).map(([regulation, data]) => (
          <div key={regulation} className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-lg">
                {regulation.toUpperCase()} Compliance
              </h4>
              <Badge className={getStatusColor(data.status)}>
                <div className="flex items-center gap-1">
                  {getStatusIcon(data.status)}
                  {data.status.toUpperCase()}
                </div>
              </Badge>
            </div>
            
            <div className="text-sm text-gray-600 mb-3">
              {data.checks_passed} of {data.total_checks} checks passed
            </div>
            
            <div className="space-y-2">
              {data.checks.map((check, index) => (
                <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(check.status)}
                    <span className="text-sm font-medium">
                      {check.check_name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {check.checked_at ? new Date(check.checked_at).toLocaleDateString() : 'Not checked'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
        
        <div className="pt-3 border-t">
          <div className="text-xs text-gray-500">
            Last updated: {new Date().toLocaleString()}
          </div>
        </div>
      </CardBody>
    </Card>
  );
};
