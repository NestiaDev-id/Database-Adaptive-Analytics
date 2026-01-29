import React, { useState } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, 
  PieChart, Pie, Cell, CartesianGrid 
} from 'recharts';
import { Download, Table as TableIcon, BarChart as BarChartIcon, PieChart as PieChartIcon } from 'lucide-react';

interface DataVisualizerProps {
  data: any[];
  headers: string[];
}

type ViewMode = 'table' | 'bar' | 'pie';

const COLORS = ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4'];

const DataVisualizer: React.FC<DataVisualizerProps> = ({ data, headers }) => {
  const [viewMode, setViewMode] = useState<ViewMode>('table');

  // Determine likely keys for chart axes
  const numericKeys = headers.filter(h => {
    // Check first few rows to see if value is numeric
    const val = data[0]?.[h];
    return !isNaN(parseFloat(val)) && isFinite(val);
  });
  
  // Use the first non-numeric key as the label, or just the first key if everything is numeric
  const labelKey = headers.find(h => !numericKeys.includes(h)) || headers[0];
  const valueKey = numericKeys[0] || headers[1]; // Default to second column if exists

  const handleDownload = () => {
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(h => `"${row[h]}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'analysis_export.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!data || data.length === 0) return null;

  return (
    <div className="mt-4 bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
      {/* Toolbar */}
      <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex flex-wrap gap-2 justify-between items-center">
        <div className="flex space-x-1 bg-slate-200 p-1 rounded-lg">
          <button
            onClick={() => setViewMode('table')}
            className={`p-1.5 rounded-md transition-all ${viewMode === 'table' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}
            title="Table View"
          >
            <TableIcon size={16} />
          </button>
          {numericKeys.length > 0 && (
            <>
              <button
                onClick={() => setViewMode('bar')}
                className={`p-1.5 rounded-md transition-all ${viewMode === 'bar' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}
                title="Bar Chart"
              >
                <BarChartIcon size={16} />
              </button>
              <button
                onClick={() => setViewMode('pie')}
                className={`p-1.5 rounded-md transition-all ${viewMode === 'pie' ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}
                title="Pie Chart"
              >
                <PieChartIcon size={16} />
              </button>
            </>
          )}
        </div>

        <button
          onClick={handleDownload}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-md transition-colors border border-indigo-200"
        >
          <Download size={14} />
          Download CSV
        </button>
      </div>

      {/* Content Area */}
      <div className="p-4 overflow-x-auto min-h-[300px] flex items-center justify-center bg-white">
        {viewMode === 'table' && (
           <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr>
                {headers.map((h) => (
                  <th key={h} className="px-4 py-2 bg-slate-100 font-semibold text-slate-700 border-b border-slate-200 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i} className="hover:bg-slate-50 border-b border-slate-100 last:border-0">
                  {headers.map((h) => (
                    <td key={h} className="px-4 py-2 text-slate-600 whitespace-nowrap">
                      {row[h]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {viewMode === 'bar' && (
          <div className="w-full h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis 
                  dataKey={labelKey} 
                  tick={{ fontSize: 12, fill: '#64748b' }} 
                  axisLine={{ stroke: '#cbd5e1' }}
                  tickLine={false}
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: '#64748b' }} 
                  axisLine={{ stroke: '#cbd5e1' }}
                  tickLine={false}
                />
                <Tooltip 
                  cursor={{ fill: '#f1f5f9' }}
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Legend />
                {numericKeys.map((key, index) => (
                  <Bar 
                    key={key} 
                    dataKey={key} 
                    fill={COLORS[index % COLORS.length]} 
                    radius={[4, 4, 0, 0]} 
                    barSize={40}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {viewMode === 'pie' && (
          <div className="w-full h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey={valueKey}
                  nameKey={labelKey}
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} strokeWidth={2} stroke="#fff" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataVisualizer;