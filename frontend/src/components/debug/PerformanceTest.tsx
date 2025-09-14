import React, { useState, useMemo } from 'react';
import DataTable, { DataTableColumn } from '../ui/DataTable';

// Generate test data
const generateTestData = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `item-${i}`,
    name: `Item ${i}`,
    status: ['active', 'inactive', 'pending'][i % 3],
    value: Math.random() * 1000,
    date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString(),
  }));
};

const PerformanceTest: React.FC = () => {
  const [dataSize, setDataSize] = useState(1000);
  const [testData] = useState(() => generateTestData(10000)); // Generate 10k items once
  
  const columns: DataTableColumn[] = [
    { key: 'id', label: 'ID', sortable: true, searchable: true },
    { key: 'name', label: 'Name', sortable: true, searchable: true },
    { key: 'status', label: 'Status', sortable: true, searchable: false },
    { key: 'value', label: 'Value', sortable: true, searchable: false },
    { key: 'date', label: 'Date', sortable: true, searchable: false },
  ];

  const currentData = useMemo(() => testData.slice(0, dataSize), [testData, dataSize]);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">DataTable Performance Test</h2>
      
      <div className="flex items-center space-x-4">
        <label className="text-sm font-medium">
          Data Size: {dataSize.toLocaleString()} items
        </label>
        <input
          type="range"
          min="100"
          max="10000"
          step="100"
          value={dataSize}
          onChange={(e) => setDataSize(Number(e.target.value))}
          className="flex-1 max-w-xs"
        />
      </div>

      <div className="text-sm text-gray-600">
        <p>Testing with {currentData.length.toLocaleString()} items</p>
        <p>Features: Search, Filter, Sort, Pagination (10 items per page)</p>
      </div>

      <DataTable
        title="Performance Test Table"
        data={currentData}
        columns={columns}
        searchPlaceholder="Search items..."
        statusFilterOptions={[
          { label: 'Active', value: 'active' },
          { label: 'Inactive', value: 'inactive' },
          { label: 'Pending', value: 'pending' },
        ]}
        onRowClick={(row) => console.log('Row clicked:', row)}
        onExport={() => console.log('Export clicked')}
        emptyState={{
          icon: () => <div className="h-12 w-12 bg-gray-200 rounded" />,
          title: 'No data',
          description: 'No test data available',
        }}
      />
    </div>
  );
};

export default PerformanceTest;
