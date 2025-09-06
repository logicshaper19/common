/**
 * Transparency Trend Chart Component
 * Shows transparency score trends over time using Recharts
 */
import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { TransparencyTrend } from '../../types/transparency';
import { Card, CardHeader, CardBody } from '../ui/Card';
import { formatTransparency } from '../../lib/utils';

interface TransparencyTrendChartProps {
  data: TransparencyTrend[];
  title?: string;
  height?: number;
  showArea?: boolean;
  className?: string;
}

const TransparencyTrendChart: React.FC<TransparencyTrendChartProps> = ({
  data,
  title = 'Transparency Trends',
  height = 300,
  showArea = false,
  className,
}) => {
  // Format data for chart
  const chartData = data.map((item) => ({
    ...item,
    date: new Date(item.date).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    }),
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-neutral-200 rounded-lg shadow-lg">
          <p className="font-medium text-neutral-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-neutral-600">{entry.name}:</span>
              <span className="text-sm font-medium text-neutral-900">
                {formatTransparency(entry.value)}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const ChartComponent = showArea ? AreaChart : LineChart;

  return (
    <Card className={className}>
      <CardHeader title={title} />
      <CardBody>
        <ResponsiveContainer width="100%" height={height}>
          <ChartComponent data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis 
              dataKey="date" 
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              domain={[0, 100]}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {showArea ? (
              <>
                <Area
                  type="monotone"
                  dataKey="overall_score"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.1}
                  strokeWidth={2}
                  name="Overall Score"
                />
                <Area
                  type="monotone"
                  dataKey="ttm_score"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.1}
                  strokeWidth={2}
                  name="TTM Score"
                />
                <Area
                  type="monotone"
                  dataKey="ttp_score"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.1}
                  strokeWidth={2}
                  name="TTP Score"
                />
              </>
            ) : (
              <>
                <Line
                  type="monotone"
                  dataKey="overall_score"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
                  name="Overall Score"
                />
                <Line
                  type="monotone"
                  dataKey="ttm_score"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: '#10b981', strokeWidth: 2, r: 3 }}
                  activeDot={{ r: 5, stroke: '#10b981', strokeWidth: 2 }}
                  name="TTM Score"
                />
                <Line
                  type="monotone"
                  dataKey="ttp_score"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={{ fill: '#f59e0b', strokeWidth: 2, r: 3 }}
                  activeDot={{ r: 5, stroke: '#f59e0b', strokeWidth: 2 }}
                  name="TTP Score"
                />
                <Line
                  type="monotone"
                  dataKey="traced_percentage"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 3 }}
                  activeDot={{ r: 5, stroke: '#8b5cf6', strokeWidth: 2 }}
                  name="Traced %"
                />
              </>
            )}
          </ChartComponent>
        </ResponsiveContainer>
      </CardBody>
    </Card>
  );
};

export default TransparencyTrendChart;
