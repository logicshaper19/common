import React from 'react';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  BarElement,
  Title, 
  Tooltip, 
  Legend, 
  ArcElement,
  Filler
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  BarElement,
  Title, 
  Tooltip, 
  Legend, 
  ArcElement,
  Filler
);

// Line Chart Component
export const LineChart = ({ data }) => {
  const chartData = {
    labels: data.data.map(item => item.x),
    datasets: [
      {
        label: data.title,
        data: data.data.map(item => item.y),
        borderColor: 'rgb(102, 126, 234)',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        borderWidth: 2,
        tension: 0.1,
        fill: true,
        pointBackgroundColor: 'rgb(102, 126, 234)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }
    ]
  };

  // Add target line if available
  if (data.data[0] && data.data[0].target) {
    chartData.datasets.push({
      label: 'Target',
      data: data.data.map(item => item.target),
      borderColor: 'rgb(255, 99, 132)',
      backgroundColor: 'rgba(255, 99, 132, 0.1)',
      borderWidth: 2,
      borderDash: [5, 5],
      pointRadius: 0,
      fill: false
    });
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: data.title,
        font: {
          size: 16,
          weight: 'bold'
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(102, 126, 234, 0.8)',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: data.x_axis || 'X Axis'
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: data.y_axis || 'Y Axis'
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ...(data.options?.scales?.y || {})
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    },
    ...data.options
  };

  return (
    <div className="chart-container">
      <div className="chart-wrapper" style={{ height: '300px' }}>
        <Line data={chartData} options={options} />
      </div>
      {data.benchmark && (
        <div className="chart-benchmark">
          <span className="benchmark-label">Benchmark:</span>
          <span className="benchmark-value">{data.benchmark}</span>
        </div>
      )}
      {data.industry_average && (
        <div className="chart-industry-avg">
          <span className="industry-label">Industry Average:</span>
          <span className="industry-value">{data.industry_average}</span>
        </div>
      )}
    </div>
  );
};

// Donut Chart Component
export const DonutChart = ({ data }) => {
  const chartData = {
    labels: data.data.map(item => item.label),
    datasets: [{
      data: data.data.map(item => item.value),
      backgroundColor: data.data.map(item => item.color),
      borderWidth: 2,
      borderColor: '#fff',
      hoverBorderWidth: 3,
      hoverBorderColor: '#fff'
    }]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          padding: 20,
          usePointStyle: true,
          font: {
            size: 12
          }
        }
      },
      title: {
        display: true,
        text: data.title,
        font: {
          size: 16,
          weight: 'bold'
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(102, 126, 234, 0.8)',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          }
        }
      }
    },
    cutout: '60%',
    ...data.options
  };

  return (
    <div className="chart-container">
      <div className="chart-wrapper" style={{ height: '300px' }}>
        <Doughnut data={chartData} options={options} />
      </div>
    </div>
  );
};

// Bar Chart Component
export const BarChart = ({ data }) => {
  const chartData = {
    labels: data.data.map(item => item.x),
    datasets: [{
      label: data.title,
      data: data.data.map(item => item.y),
      backgroundColor: data.data.map(item => item.color || 'rgba(102, 126, 234, 0.8)'),
      borderColor: data.data.map(item => item.color || 'rgb(102, 126, 234)'),
      borderWidth: 1,
      borderRadius: 4,
      borderSkipped: false
    }]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: data.title,
        font: {
          size: 16,
          weight: 'bold'
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(102, 126, 234, 0.8)',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: data.x_axis || 'X Axis'
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      },
      y: {
        display: true,
        title: {
          display: true,
          text: data.y_axis || 'Y Axis'
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ...(data.options?.scales?.y || {})
      }
    },
    ...data.options
  };

  return (
    <div className="chart-container">
      <div className="chart-wrapper" style={{ height: '300px' }}>
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
};

// Gauge Chart Component (Custom implementation)
export const GaugeChart = ({ data }) => {
  const value = data.value || 0;
  const min = data.min || 0;
  const max = data.max || 100;
  const percentage = ((value - min) / (max - min)) * 100;
  
  // Determine color based on ranges
  let color = '#4caf50'; // default green
  if (data.ranges) {
    for (const range of data.ranges) {
      if (value >= range.min && value <= range.max) {
        color = range.color;
        break;
      }
    }
  }

  return (
    <div className="chart-container gauge-chart">
      <div className="gauge-wrapper">
        <div className="gauge-title">{data.title}</div>
        <div className="gauge-container">
          <svg width="200" height="120" viewBox="0 0 200 120">
            {/* Background arc */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke="#e0e0e0"
              strokeWidth="20"
              strokeLinecap="round"
            />
            {/* Value arc */}
            <path
              d="M 20 100 A 80 80 0 0 1 180 100"
              fill="none"
              stroke={color}
              strokeWidth="20"
              strokeLinecap="round"
              strokeDasharray={`${percentage * 2.51} 251`}
              strokeDashoffset="62.75"
              style={{ transition: 'stroke-dasharray 0.5s ease' }}
            />
            {/* Center circle */}
            <circle cx="100" cy="100" r="8" fill={color} />
          </svg>
          <div className="gauge-value">
            <span className="value-number">{value}</span>
            <span className="value-unit">{data.unit || ''}</span>
          </div>
          {data.target && (
            <div className="gauge-target">
              Target: {data.target}{data.unit || ''}
            </div>
          )}
        </div>
        {data.ranges && (
          <div className="gauge-ranges">
            {data.ranges.map((range, index) => (
              <div key={index} className="range-item">
                <div 
                  className="range-color" 
                  style={{ backgroundColor: range.color }}
                ></div>
                <span className="range-label">{range.label}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Data Table Component
export const DataTable = ({ data }) => {
  const [sortConfig, setSortConfig] = React.useState({ key: null, direction: 'asc' });
  const [filteredRows, setFilteredRows] = React.useState(data.rows || []);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [searchTerm, setSearchTerm] = React.useState('');

  const itemsPerPage = 10;

  // Sorting functionality
  const handleSort = (key) => {
    if (!data.sortable) return;
    
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });

    const sortedRows = [...filteredRows].sort((a, b) => {
      const aVal = a[key];
      const bVal = b[key];
      
      if (aVal < bVal) return direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return direction === 'asc' ? 1 : -1;
      return 0;
    });
    
    setFilteredRows(sortedRows);
  };

  // Search functionality
  React.useEffect(() => {
    if (!searchTerm) {
      setFilteredRows(data.rows || []);
    } else {
      const filtered = (data.rows || []).filter(row =>
        row.some(cell => 
          cell.toString().toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
      setFilteredRows(filtered);
    }
    setCurrentPage(1);
  }, [searchTerm, data.rows]);

  // Pagination
  const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentRows = filteredRows.slice(startIndex, endIndex);

  const getHighlightClass = (cell, rowIndex) => {
    if (!data.highlight_rules) return '';
    
    for (const [rule, className] of Object.entries(data.highlight_rules)) {
      if (cell.toString().toLowerCase().includes(rule.toLowerCase())) {
        return `highlight-${className}`;
      }
    }
    return '';
  };

  return (
    <div className="table-container">
      <div className="table-header">
        <h3 className="table-title">{data.title}</h3>
        {data.filterable && (
          <div className="table-search">
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>
        )}
      </div>
      
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              {data.headers.map((header, index) => (
                <th 
                  key={index}
                  className={data.sortable ? 'sortable' : ''}
                  onClick={() => handleSort(index)}
                >
                  {header}
                  {data.sortable && (
                    <span className="sort-indicator">
                      {sortConfig.key === index && (
                        sortConfig.direction === 'asc' ? '↑' : '↓'
                      )}
                    </span>
                  )}
                </th>
              ))}
              {data.actions && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {currentRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td 
                    key={cellIndex}
                    className={getHighlightClass(cell, rowIndex)}
                  >
                    {cell}
                  </td>
                ))}
                {data.actions && (
                  <td className="actions-cell">
                    {data.actions.map((action, actionIndex) => (
                      <button 
                        key={actionIndex} 
                        className="table-action"
                        onClick={() => console.log(`Action: ${action} on row ${rowIndex}`)}
                      >
                        {action}
                      </button>
                    ))}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {data.pagination && totalPages > 1 && (
        <div className="table-pagination">
          <button 
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="pagination-btn"
          >
            Previous
          </button>
          <span className="pagination-info">
            Page {currentPage} of {totalPages} ({filteredRows.length} items)
          </span>
          <button 
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="pagination-btn"
          >
            Next
          </button>
        </div>
      )}
      
      {data.exportable && (
        <div className="table-export">
          <button 
            className="export-btn"
            onClick={() => {
              // Export functionality would go here
              console.log('Export table data');
            }}
          >
            Export Data
          </button>
        </div>
      )}
    </div>
  );
};

// Metric Cards Component
export const MetricCards = ({ data }) => {
  return (
    <div className="metric-cards">
      <h3 className="metric-cards-title">{data.title}</h3>
      <div className="cards-grid">
        {data.metrics.map((metric, index) => (
          <div key={index} className={`metric-card ${metric.color}`}>
            <div className="metric-icon">{metric.icon}</div>
            <div className="metric-content">
              <div className="metric-value">{metric.value}</div>
              <div className="metric-label">{metric.label}</div>
              <div className="metric-trend">
                <span className={`trend-${metric.trend.startsWith('+') ? 'positive' : metric.trend.startsWith('-') ? 'negative' : 'neutral'}`}>
                  {metric.trend}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Network Graph Component (Simplified implementation)
export const NetworkGraph = ({ data }) => {
  const [selectedNode, setSelectedNode] = React.useState(null);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  return (
    <div className="network-graph-container">
      <div className="graph-header">
        <h3 className="graph-title">{data.title}</h3>
        {selectedNode && (
          <div className="node-info">
            <strong>{selectedNode.label}</strong>
            <span className="node-type">({selectedNode.type})</span>
            {selectedNode.transparency && (
              <span className="transparency-score">
                Transparency: {selectedNode.transparency}%
              </span>
            )}
          </div>
        )}
      </div>
      
      <div className="graph-visualization">
        <svg width="100%" height="400" viewBox="0 0 800 400">
          {/* Render edges first (so they appear behind nodes) */}
          {data.edges.map((edge, index) => {
            const fromNode = data.nodes.find(n => n.id === edge.from);
            const toNode = data.nodes.find(n => n.id === edge.to);
            
            if (!fromNode || !toNode) return null;
            
            // Simple positioning (in a real implementation, you'd use a proper layout algorithm)
            const fromX = 100 + (index * 150);
            const toX = 200 + (index * 150);
            const fromY = 200;
            const toY = 200;
            
            return (
              <g key={index}>
                <line
                  x1={fromX}
                  y1={fromY}
                  x2={toX}
                  y2={toY}
                  stroke="#ccc"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                />
                <text
                  x={(fromX + toX) / 2}
                  y={(fromY + toY) / 2 - 10}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#666"
                >
                  {edge.label}
                </text>
              </g>
            );
          })}
          
          {/* Render nodes */}
          {data.nodes.map((node, index) => {
            const x = 100 + (index * 150);
            const y = 200;
            const size = node.size || 15;
            
            return (
              <g key={node.id}>
                <circle
                  cx={x}
                  cy={y}
                  r={size}
                  fill={node.type === 'company' ? '#667eea' : 
                        node.type === 'supplier' ? '#4caf50' : 
                        node.type === 'customer' ? '#ff9800' : '#9c27b0'}
                  stroke="#fff"
                  strokeWidth="2"
                  onClick={() => handleNodeClick(node)}
                  style={{ cursor: 'pointer' }}
                />
                <text
                  x={x}
                  y={y + size + 20}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#333"
                >
                  {node.label}
                </text>
              </g>
            );
          })}
          
          {/* Arrow marker definition */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill="#ccc"
              />
            </marker>
          </defs>
        </svg>
      </div>
      
      <div className="graph-legend">
        <div className="legend-item">
          <div className="legend-color company"></div>
          <span>Your Company</span>
        </div>
        <div className="legend-item">
          <div className="legend-color supplier"></div>
          <span>Suppliers</span>
        </div>
        <div className="legend-item">
          <div className="legend-color customer"></div>
          <span>Customers</span>
        </div>
      </div>
    </div>
  );
};
