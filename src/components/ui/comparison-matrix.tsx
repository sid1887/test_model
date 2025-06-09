
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Save, X, ArrowDown, ArrowUp, Star, Award, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useAccessibility } from '@/hooks/useAccessibility';

interface Product {
  id: string;
  name: string;
  price: string;
  originalPrice?: string;
  image: string;
  store: string;
  valueScore: number;
  specs: string;
  priceChange: number;
}

interface ComparisonMatrixProps {
  products: Product[];
  onSave: () => void;
  onRemove: (id: string) => void;
}

const ComparisonMatrix: React.FC<ComparisonMatrixProps> = ({
  products,
  onSave,
  onRemove
}) => {
  const [sortBy, setSortBy] = useState<'price' | 'valueScore' | 'priceChange'>('valueScore');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [isMobileView, setIsMobileView] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const { announce, getAriaProps, getKeyboardProps } = useAccessibility();

  // Check if mobile view should be used
  React.useEffect(() => {
    const checkMobileView = () => {
      setIsMobileView(window.innerWidth < 768);
    };
    
    checkMobileView();
    window.addEventListener('resize', checkMobileView);
    return () => window.removeEventListener('resize', checkMobileView);
  }, []);

  const handleSort = (column: 'price' | 'valueScore' | 'priceChange') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
    announce(`Sorted by ${column} in ${sortOrder === 'asc' ? 'descending' : 'ascending'} order`);
  };

  const toggleRowExpansion = (productId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(productId)) {
      newExpanded.delete(productId);
    } else {
      newExpanded.add(productId);
    }
    setExpandedRows(newExpanded);
  };

  const sortedProducts = [...products].sort((a, b) => {
    let aValue: number, bValue: number;
    
    switch (sortBy) {
      case 'price':
        aValue = parseFloat(a.price.replace(/[$,]/g, ''));
        bValue = parseFloat(b.price.replace(/[$,]/g, ''));
        break;
      case 'valueScore':
        aValue = a.valueScore;
        bValue = b.valueScore;
        break;
      case 'priceChange':
        aValue = a.priceChange;
        bValue = b.priceChange;
        break;
      default:
        aValue = bValue = 0;
    }
    
    return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
  });

  const getBestPrice = () => {
    const prices = products.map(p => parseFloat(p.price.replace(/[$,]/g, '')));
    return Math.min(...prices);
  };

  const getBestValueScore = () => {
    const scores = products.map(p => p.valueScore);
    return Math.max(...scores);
  };

  const bestPrice = getBestPrice();
  const bestValueScore = getBestValueScore();

  const SortableHeader = ({ label, sortKey, children }: { 
    label: string; 
    sortKey: 'price' | 'valueScore' | 'priceChange';
    children: React.ReactNode;
  }) => (
    <th 
      className="text-left p-4 font-semibold cursor-pointer hover:bg-accent transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50"
      onClick={() => handleSort(sortKey)}
      {...getAriaProps(`Sort by ${label}`)}
      {...getKeyboardProps(() => handleSort(sortKey))}
      tabIndex={0}
    >
      <div className="flex items-center gap-2">
        {children}
        <motion.div
          animate={{ 
            rotate: sortBy === sortKey && sortOrder === 'asc' ? 0 : 180,
            opacity: sortBy === sortKey ? 1 : 0.5
          }}
          transition={{ duration: 0.2 }}
        >
          <ArrowDown className="w-4 h-4" />
        </motion.div>
      </div>
    </th>
  );

  const MobileProductCard = ({ product, index }: { product: Product; index: number }) => {
    const productPrice = parseFloat(product.price.replace(/[$,]/g, ''));
    const isBestPrice = productPrice === bestPrice;
    const isBestValue = product.valueScore === bestValueScore;
    const hasDropPrediction = product.priceChange < -2;
    const isExpanded = expandedRows.has(product.id);

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
        className="border border-border rounded-lg overflow-hidden"
      >
        {/* Header - Always Visible */}
        <div 
          className="p-4 bg-muted/25 cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => toggleRowExpansion(product.id)}
          {...getAriaProps(`${isExpanded ? 'Collapse' : 'Expand'} details for ${product.name}`)}
          {...getKeyboardProps(() => toggleRowExpansion(product.id))}
          tabIndex={0}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img
                src={product.image}
                alt={product.name}
                className="w-12 h-12 object-cover rounded-lg"
              />
              <div>
                <h4 className="font-semibold text-sm line-clamp-1">
                  {product.name}
                </h4>
                <div className="font-bold text-lg text-green-600 mt-1">
                  {product.price}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {(isBestPrice || isBestValue) && (
                <div className="flex gap-1">
                  {isBestPrice && <Award className="w-4 h-4 text-green-500" />}
                  {isBestValue && <Star className="w-4 h-4 text-yellow-500 fill-current" />}
                </div>
              )}
              <motion.div
                animate={{ rotate: isExpanded ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronDown className="w-5 h-5" />
              </motion.div>
            </div>
          </div>
        </div>

        {/* Expanded Content */}
        <motion.div
          initial={false}
          animate={{ 
            height: isExpanded ? 'auto' : 0,
            opacity: isExpanded ? 1 : 0
          }}
          transition={{ duration: 0.3 }}
          className="overflow-hidden"
        >
          <div className="p-4 space-y-4 border-t border-border">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-muted-foreground">Retailer</span>
                <div className="mt-1">
                  <span className="px-2 py-1 bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-medium rounded-full border border-blue-500/20">
                    {product.store}
                  </span>
                </div>
              </div>
              
              <div>
                <span className="text-sm text-muted-foreground">Value Score</span>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex items-center gap-1 px-2 py-1 rounded-full text-white font-semibold text-sm bg-gradient-to-r from-yellow-500 to-orange-500">
                    <Star className="w-3 h-3 fill-current" />
                    <span>{product.valueScore}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-muted-foreground">7-day Change</span>
                <div className={cn(
                  "flex items-center gap-1 font-semibold mt-1",
                  product.priceChange < 0 ? "text-green-600" : "text-red-600"
                )}>
                  <span>
                    {product.priceChange < 0 ? '↓' : '↑'} {Math.abs(product.priceChange)}%
                  </span>
                </div>
              </div>
              
              <div className="flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemove(product.id)}
                  className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
                  {...getAriaProps(`Remove ${product.name} from comparison`)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div>
              <span className="text-sm text-muted-foreground">Key Specs</span>
              <div className="text-sm mt-1 line-clamp-2">
                {product.specs}
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full"
    >
      <Card className="overflow-hidden backdrop-blur-md bg-white/90 dark:bg-black/80 border border-white/20 dark:border-white/10 shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-border flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Product Comparison
            </h3>
            <p className="text-muted-foreground mt-1">
              Compare {products.length} selected products
            </p>
          </div>
          
          <div className="flex gap-3">
            <Button
              onClick={onSave}
              className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 focus:ring-2 focus:ring-green-500/50"
              {...getAriaProps('Save comparison for later')}
            >
              <Save className="w-4 h-4 mr-2" />
              Save Comparison
            </Button>
          </div>
        </div>

        {/* Content */}
        {isMobileView ? (
          // Mobile Accordion View
          <div className="p-4 space-y-4">
            {sortedProducts.map((product, index) => (
              <MobileProductCard key={product.id} product={product} index={index} />
            ))}
          </div>
        ) : (
          // Desktop Table View
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left p-4 font-semibold">Product</th>
                  <th className="text-left p-4 font-semibold">Retailer</th>
                  <SortableHeader label="Price" sortKey="price">
                    Price
                  </SortableHeader>
                  <SortableHeader label="Value Score" sortKey="valueScore">
                    Value Score
                  </SortableHeader>
                  <SortableHeader label="7-day Change" sortKey="priceChange">
                    <div className="flex items-center gap-1">
                      7-day Δ
                      <button
                        className="text-muted-foreground hover:text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50 rounded"
                        {...getAriaProps('7-day forecasted change vs. today')}
                        {...getKeyboardProps(() => announce('7-day forecasted change vs. today'))}
                      >
                        <Info className="w-3 h-3" />
                      </button>
                    </div>
                  </SortableHeader>
                  <th className="text-left p-4 font-semibold">Key Specs</th>
                  <th className="text-center p-4 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedProducts.map((product, index) => {
                  const productPrice = parseFloat(product.price.replace(/[$,]/g, ''));
                  const isBestPrice = productPrice === bestPrice;
                  const isBestValue = product.valueScore === bestValueScore;
                  const hasDropPrediction = product.priceChange < -2;

                  return (
                    <motion.tr
                      key={product.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="border-b border-border hover:bg-accent/50 transition-colors focus-within:bg-accent/25"
                    >
                      {/* Product mini-card */}
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <img
                            src={product.image}
                            alt={product.name}
                            className="w-12 h-12 object-cover rounded-lg"
                          />
                          <div>
                            <h4 className="font-semibold text-sm line-clamp-2 max-w-48">
                              {product.name}
                            </h4>
                          </div>
                        </div>
                      </td>

                      {/* Retailer */}
                      <td className="p-4">
                        <span className="px-2 py-1 bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-medium rounded-full border border-blue-500/20">
                          {product.store}
                        </span>
                      </td>

                      {/* Price */}
                      <td className="p-4">
                        <div className={cn(
                          "relative",
                          isBestPrice && "ring-2 ring-green-500 rounded-lg p-2 bg-green-500/10"
                        )}>
                          <div className="font-bold text-lg text-green-600">
                            {product.price}
                          </div>
                          {product.originalPrice && (
                            <div className="text-sm text-muted-foreground line-through">
                              {product.originalPrice}
                            </div>
                          )}
                          {isBestPrice && (
                            <div className="absolute -top-2 -right-2">
                              <Award className="w-5 h-5 text-green-500" />
                            </div>
                          )}
                        </div>
                      </td>

                      {/* Value Score */}
                      <td className="p-4">
                        <div className={cn(
                          "flex items-center gap-2",
                          isBestValue && "relative"
                        )}>
                          <div className="flex items-center gap-1 px-2 py-1 rounded-full text-white font-semibold text-sm bg-gradient-to-r from-yellow-500 to-orange-500">
                            <Star className="w-3 h-3 fill-current" />
                            <span>{product.valueScore}</span>
                          </div>
                          {isBestValue && (
                            <motion.div
                              animate={{ scale: [1, 1.2, 1] }}
                              transition={{ duration: 1, repeat: Infinity }}
                            >
                              <Star className="w-5 h-5 text-yellow-500 fill-current" />
                            </motion.div>
                          )}
                        </div>
                      </td>

                      {/* Price Change */}
                      <td className="p-4">
                        <div className={cn(
                          "flex items-center gap-1 font-semibold",
                          product.priceChange < 0 ? "text-green-600" : "text-red-600",
                          hasDropPrediction && "relative"
                        )}>
                          <span>
                            {product.priceChange < 0 ? '↓' : '↑'} {Math.abs(product.priceChange)}%
                          </span>
                          {hasDropPrediction && (
                            <motion.div
                              animate={{ y: [0, -2, 0] }}
                              transition={{ duration: 0.5, repeat: Infinity }}
                              className="text-red-500"
                            >
                              <ArrowDown className="w-4 h-4" />
                            </motion.div>
                          )}
                        </div>
                      </td>

                      {/* Specs */}
                      <td className="p-4">
                        <div className="text-sm text-muted-foreground max-w-48 line-clamp-2">
                          {product.specs}
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="p-4 text-center">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onRemove(product.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950 focus:ring-2 focus:ring-red-500/50"
                          {...getAriaProps(`Remove ${product.name} from comparison`)}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </td>
                    </motion.tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Legend */}
        <div className="p-6 border-t border-border bg-muted/25">
          <div className="flex flex-wrap gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 border-2 border-green-500 rounded bg-green-500/10"></div>
              <span>Best Price</span>
            </div>
            <div className="flex items-center gap-2">
              <Star className="w-4 h-4 text-yellow-500 fill-current" />
              <span>Best Value Score</span>
            </div>
            <div className="flex items-center gap-2">
              <ArrowDown className="w-4 h-4 text-red-500" />
              <span>Predicted Price Drop</span>
            </div>
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4" />
              <span>Click column headers to sort</span>
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export { ComparisonMatrix };
