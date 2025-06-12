
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceDot } from 'recharts';
import { Download, Calendar, Loader2, Info, Eye, EyeOff } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useAccessibility } from '@/hooks/useAccessibility';
import { Product, ChartDataPoint } from '@/types/product';

interface TrendChartProps {
  products: Product[];
}

interface CombinedDataPoint {
  date: string;
  annotation?: ChartDataPoint['annotation'];
  [key: string]: string | number | null | ChartDataPoint['annotation'] | undefined;
}

interface CsvRow {
  Date: string;
  [key: string]: string | number;
}

interface TooltipPayload {
  value: number | null;
  name: string;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

interface AnnotationDotProps {
  cx?: number;
  cy?: number;
  payload?: CombinedDataPoint;
}

const TrendChart: React.FC<TrendChartProps> = ({ products }) => {
  const [dateRange, setDateRange] = useState<'7d' | '14d' | '30d'>('30d');
  const [isUpdating, setIsUpdating] = useState(false);
  const [showLegend, setShowLegend] = useState(true);
  const [isMobileView, setIsMobileView] = useState(false);
  const [selectedAnnotation, setSelectedAnnotation] = useState<ChartDataPoint['annotation'] | null>(null);

  const { announce, getAriaProps, getKeyboardProps } = useAccessibility();

  // Check if mobile view should be used
  React.useEffect(() => {
    const checkMobileView = () => {
      setIsMobileView(window.innerWidth < 768);
      if (window.innerWidth < 768) {
        setShowLegend(false);
      }
    };
    
    checkMobileView();
    window.addEventListener('resize', checkMobileView);
    return () => window.removeEventListener('resize', checkMobileView);
  }, []);

  // Combine all product data for the chart
  const combinedData = React.useMemo(() => {
    if (products.length === 0) return [];

    // Get all unique dates
    const allDates = new Set<string>();
    products.forEach(product => {
      product.chartData.forEach(point => allDates.add(point.date));
    });

    // Sort dates
    const sortedDates = Array.from(allDates).sort();    // Create combined data points
    return sortedDates.map(date => {
      const dataPoint: CombinedDataPoint = { date };
      let annotation: ChartDataPoint['annotation'] | undefined;
      
      products.forEach(product => {
        const point = product.chartData.find(p => p.date === date);
        if (point) {
          dataPoint[`${product.name}_actual`] = point.actual;
          dataPoint[`${product.name}_predicted`] = point.predicted;
          if (point.annotation && !annotation) {
            annotation = point.annotation;
          }
        }
      });
      
      if (annotation) {
        dataPoint.annotation = annotation;
      }
      
      return dataPoint;
    });
  }, [products]);

  const handleDateRangeChange = (range: '7d' | '14d' | '30d') => {
    setDateRange(range);
    setIsUpdating(true);
    announce(`Date range changed to ${range}`);
    
    // Simulate data update
    setTimeout(() => {
      setIsUpdating(false);
      announce('Chart data updated');
    }, 1000);
  };  const handleDownloadCSV = () => {
    const csvData = combinedData.map(point => {
      const row: CsvRow = { Date: point.date };
      products.forEach(product => {
        const actualValue = point[`${product.name}_actual`];
        const predictedValue = point[`${product.name}_predicted`];
        row[`${product.name} (Actual)`] = (typeof actualValue === 'number' ? actualValue : '');
        row[`${product.name} (Predicted)`] = (typeof predictedValue === 'number' ? predictedValue : '');
      });
      return row;
    });

    const headers = ['Date'];
    products.forEach(product => {
      headers.push(`${product.name} (Actual)`, `${product.name} (Predicted)`);
    });

    const csvContent = [
      headers.join(','),
      ...csvData.map(row => headers.map(header => row[header]).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'price-trends.csv';
    a.click();
    URL.revokeObjectURL(url);
    announce('CSV file downloaded');
  };
  const formatTooltip = (value: number | null, name: string) => {
    if (value === null) return ['No data', name];
    return [`$${value}`, name];
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getLineColor = (index: number) => {
    const colors = ['#3b82f6', '#8b5cf6', '#ef4444', '#10b981', '#f59e0b'];
    return colors[index % colors.length];
  };
  const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
    if (active && payload && payload.length && label) {
      const dataPoint = combinedData.find(d => d.date === label);
      
      return (
        <div className="bg-popover border border-border rounded-lg p-3 shadow-lg">
          <p className="font-semibold mb-2">{`Date: ${formatDate(label)}`}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {`${entry.name}: $${entry.value}`}
            </p>
          ))}
          {dataPoint?.annotation && (
            <div className="mt-2 pt-2 border-t border-border">
              <p className="text-xs font-semibold text-blue-600">{dataPoint.annotation.label}</p>
              <p className="text-xs text-muted-foreground">{dataPoint.annotation.description}</p>
            </div>
          )}
        </div>
      );
    }
    return null;
  };
  const AnnotationDot: React.FC<AnnotationDotProps> = ({ cx, cy, payload }) => {
    if (!payload?.annotation) return null;
    
    return (
      <g>
        <circle
          cx={cx}
          cy={cy}
          r={6}
          fill="#3b82f6"
          stroke="#ffffff"
          strokeWidth={2}
          className="cursor-pointer hover:r-8 transition-all"
          onClick={() => setSelectedAnnotation(payload.annotation || null)}
        />
        <circle
          cx={cx}
          cy={cy}
          r={3}
          fill="#ffffff"
        />
      </g>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full"
    >
      <Card className="overflow-hidden backdrop-blur-md bg-white/90 dark:bg-black/80 border border-white/20 dark:border-white/10 shadow-2xl">
        {/* Header with Controls */}
        <div className="p-6 border-b border-border">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Price Trend Analysis
              </h3>
              <p className="text-muted-foreground mt-1">
                Historical and predicted price movements
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Date Range Selector */}
              <div className="flex items-center gap-1 p-1 bg-muted rounded-lg">
                {(['7d', '14d', '30d'] as const).map((range) => (
                  <button
                    key={range}
                    onClick={() => handleDateRangeChange(range)}
                    className={cn(
                      "px-3 py-1 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50",
                      dateRange === range
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-accent"
                    )}
                    {...getAriaProps(`Set date range to ${range}`)}
                    {...getKeyboardProps(() => handleDateRangeChange(range))}
                  >
                    {range}
                  </button>
                ))}
              </div>

              {/* Legend Toggle for Mobile */}
              {isMobileView && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowLegend(!showLegend)}
                  className="flex items-center gap-2"
                  {...getAriaProps(`${showLegend ? 'Hide' : 'Show'} legend`)}
                >
                  {showLegend ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  Legend
                </Button>
              )}

              {/* Download Button */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownloadCSV}
                className="flex items-center gap-2 focus:ring-2 focus:ring-primary/50"
                {...getAriaProps('Download chart data as CSV')}
              >
                <Download className="w-4 h-4" />
                CSV
              </Button>
            </div>
          </div>

          {/* Update Indicator */}
          {isUpdating && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 flex items-center gap-2 text-sm text-muted-foreground"
            >
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Updating chart data...</span>
            </motion.div>
          )}
        </div>

        {/* Chart Container */}
        <div className="p-6">
          <div className="relative">
            {isUpdating && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-10 rounded-lg"
              >
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Updating chart data...</span>
                </div>
              </motion.div>
            )}

            <ResponsiveContainer width="100%" height={isMobileView ? 300 : 400}>
              <LineChart 
                data={combinedData} 
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={formatDate}
                  className="text-xs"
                />
                <YAxis 
                  tickFormatter={(value) => `$${value}`}
                  className="text-xs"
                />
                <Tooltip content={<CustomTooltip />} />
                {(!isMobileView || showLegend) && (
                  <Legend 
                    wrapperStyle={{
                      paddingTop: '20px',
                      fontSize: '12px'
                    }}
                  />
                )}

                {/* Render lines for each product */}
                {products.map((product, index) => (
                  <React.Fragment key={product.id}>
                    {/* Actual price line - thicker */}
                    <Line
                      type="monotone"
                      dataKey={`${product.name}_actual`}
                      stroke={getLineColor(index)}
                      strokeWidth={4}
                      dot={{ fill: getLineColor(index), strokeWidth: 2, r: 5 }}
                      connectNulls={false}
                      name={`${product.name} (Actual)`}
                    />
                    {/* Predicted price line - thinner, dashed */}
                    <Line
                      type="monotone"
                      dataKey={`${product.name}_predicted`}
                      stroke={getLineColor(index)}
                      strokeWidth={2}
                      strokeDasharray="8 4"
                      dot={{ fill: getLineColor(index), strokeWidth: 2, r: 3 }}
                      connectNulls={false}
                      name={`${product.name} (Predicted)`}
                    />
                  </React.Fragment>
                ))}                {/* Annotation dots */}
                {combinedData.map((dataPoint, index) => {
                  if (!dataPoint.annotation) return null;
                  
                  // Find the first non-null value for positioning
                  let yValue: number | null = null;
                  for (const product of products) {
                    const actualValue = dataPoint[`${product.name}_actual`];
                    const predictedValue = dataPoint[`${product.name}_predicted`];
                    if (typeof actualValue === 'number') {
                      yValue = actualValue;
                      break;
                    } else if (typeof predictedValue === 'number') {
                      yValue = predictedValue;
                      break;
                    }
                  }
                  
                  if (yValue === null) return null;
                  
                  return (
                    <ReferenceDot
                      key={index}
                      x={dataPoint.date}
                      y={yValue}
                      shape={<AnnotationDot />}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Enhanced Legend */}
        <div className="px-6 pb-6">
          <div className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <div className="w-6 h-1 bg-blue-500 rounded"></div>
              <span>Actual Price</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-1 bg-blue-500 rounded border-dashed border-t-2 border-blue-500"></div>
              <span>Predicted Price</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full border-2 border-white"></div>
              <span>Price Events</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              <span>Last 30 days + 7-day forecast</span>
            </div>
            <button
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 rounded"
              {...getAriaProps('Chart help and explanation')}
              {...getKeyboardProps(() => announce('This chart shows historical prices as solid lines and predicted prices as dashed lines. Click on blue dots to see price event details.'))}
            >
              <Info className="w-4 h-4" />
              <span>Help</span>
            </button>
          </div>
        </div>

        {/* Annotation Modal */}
        {selectedAnnotation && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setSelectedAnnotation(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-background border border-border rounded-lg p-6 max-w-sm w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h4 className="font-semibold text-lg mb-2">{selectedAnnotation.label}</h4>
              <p className="text-muted-foreground mb-4">{selectedAnnotation.description}</p>
              <Button
                onClick={() => setSelectedAnnotation(null)}
                className="w-full"
                {...getAriaProps('Close annotation details')}
              >
                Close
              </Button>
            </motion.div>
          </motion.div>
        )}
      </Card>
    </motion.div>
  );
};

export { TrendChart };
