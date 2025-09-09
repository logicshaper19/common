import React from 'react';
import { 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  XCircle, 
  Package, 
  Truck, 
  FileText,
  UserCheck
} from 'lucide-react';

interface PurchaseOrderStatusBadgeProps {
  status: string;
  className?: string;
}

const PurchaseOrderStatusBadge: React.FC<PurchaseOrderStatusBadgeProps> = ({ 
  status, 
  className = '' 
}) => {
  const getStatusConfig = (status: string) => {
    switch (status.toLowerCase()) {
      case 'draft':
        return {
          label: 'Draft',
          icon: FileText,
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          iconColor: 'text-gray-600'
        };
      case 'pending':
        return {
          label: 'Pending',
          icon: Clock,
          bgColor: 'bg-yellow-100',
          textColor: 'text-yellow-800',
          iconColor: 'text-yellow-600'
        };
      case 'awaiting_buyer_approval':
        return {
          label: 'Awaiting Approval',
          icon: UserCheck,
          bgColor: 'bg-amber-100',
          textColor: 'text-amber-800',
          iconColor: 'text-amber-600'
        };
      case 'confirmed':
        return {
          label: 'Confirmed',
          icon: CheckCircle,
          bgColor: 'bg-green-100',
          textColor: 'text-green-800',
          iconColor: 'text-green-600'
        };
      case 'in_transit':
        return {
          label: 'In Transit',
          icon: Truck,
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-800',
          iconColor: 'text-blue-600'
        };
      case 'shipped':
        return {
          label: 'Shipped',
          icon: Package,
          bgColor: 'bg-indigo-100',
          textColor: 'text-indigo-800',
          iconColor: 'text-indigo-600'
        };
      case 'delivered':
        return {
          label: 'Delivered',
          icon: CheckCircle,
          bgColor: 'bg-emerald-100',
          textColor: 'text-emerald-800',
          iconColor: 'text-emerald-600'
        };
      case 'received':
        return {
          label: 'Received',
          icon: CheckCircle,
          bgColor: 'bg-teal-100',
          textColor: 'text-teal-800',
          iconColor: 'text-teal-600'
        };
      case 'cancelled':
        return {
          label: 'Cancelled',
          icon: XCircle,
          bgColor: 'bg-red-100',
          textColor: 'text-red-800',
          iconColor: 'text-red-600'
        };
      case 'declined':
        return {
          label: 'Declined',
          icon: XCircle,
          bgColor: 'bg-red-100',
          textColor: 'text-red-800',
          iconColor: 'text-red-600'
        };
      case 'amendment_pending':
        return {
          label: 'Amendment Pending',
          icon: AlertTriangle,
          bgColor: 'bg-orange-100',
          textColor: 'text-orange-800',
          iconColor: 'text-orange-600'
        };
      default:
        return {
          label: status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' '),
          icon: Clock,
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          iconColor: 'text-gray-600'
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor} ${className}`}>
      <Icon className={`w-3 h-3 mr-1 ${config.iconColor}`} />
      {config.label}
    </span>
  );
};

export default PurchaseOrderStatusBadge;
