import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, Loader2, ChevronDown, ChevronUp, Filter, WifiOff } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export interface SearchFilters {
  category?: string;
  store?: string;
  minPrice?: number;
  maxPrice?: number;
  location?: string;
  currency?: string;
  sortBy?: 'price' | 'rating' | 'popularity';
  sortOrder?: 'asc' | 'desc';
}

interface SearchBarProps {
  placeholder?: string;
  onSearch: (query: string, filters: SearchFilters) => void;
  isLoading?: boolean;
  isOffline?: boolean;
  className?: string;
  showFilters?: boolean;
}

const CATEGORIES = [
  'All Categories',
  'Electronics',
  'Computers',
  'Mobiles',
  'TV & Video',
  'Audio',
  'Appliances',
  'Furniture',
  'Gaming',
];

const STORES = [
  { value: '', label: 'All Stores' },
  { value: 'amazon', label: 'Amazon' },
  { value: 'flipkart', label: 'Flipkart' },
  { value: 'croma', label: 'Croma' },
];

const SORT_OPTIONS = [
  { value: 'rating-desc', label: 'Highest Rated' },
  { value: 'price-asc', label: 'Price: Low to High' },
  { value: 'price-desc', label: 'Price: High to Low' },
  { value: 'popularity-desc', label: 'Most Popular' },
];

export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = 'Search products, brands or stores...',
  onSearch,
  isLoading = false,
  isOffline = false,
  className,
  showFilters: initialShowFilters = false,
}) => {
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(initialShowFilters);
  const [filters, setFilters] = useState<SearchFilters>({
    category: '',
    store: '',
    sortBy: 'rating',
    sortOrder: 'desc',
  });
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSearch = () => {
    if (query.trim() || Object.values(filters).some(v => v)) {
      onSearch(query.trim(), filters);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleClear = () => {
    setQuery('');
    setFilters({
      category: '',
      store: '',
      sortBy: 'rating',
      sortOrder: 'desc',
    });
    inputRef.current?.focus();
  };

  const updateFilter = (key: keyof SearchFilters, value: string | number) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleSortChange = (value: string) => {
    const [sortBy, sortOrder] = value.split('-') as [SearchFilters['sortBy'], SearchFilters['sortOrder']];
    setFilters(prev => ({ ...prev, sortBy, sortOrder }));
  };

  const activeFilterCount = Object.entries(filters).filter(
    ([key, value]) => value && key !== 'sortBy' && key !== 'sortOrder'
  ).length;

  return (
    <div className={cn("w-full max-w-4xl mx-auto", className)}>
      {/* Main Search Container */}
      <Card className="relative overflow-hidden backdrop-blur-sm bg-card/95 border-2 border-border/50 shadow-xl hover:shadow-2xl transition-all duration-300">
        <div className="flex items-center gap-2 p-2">
          {/* Search Icon */}
          <div className="pl-2">
            {isLoading ? (
              <Loader2 className="h-5 w-5 text-primary animate-spin" />
            ) : (
              <Search className="h-5 w-5 text-muted-foreground" />
            )}
          </div>

          {/* Search Input */}
          <Input
            ref={inputRef}
            type="text"
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-1 border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 text-base"
            disabled={isLoading}
            aria-label="Search products"
          />

          {/* Status Indicators */}
          <div className="flex items-center gap-2">
            {/* Offline Status Chip */}
            {isOffline && (
              <Badge variant="secondary" className="flex items-center gap-1 text-xs">
                <WifiOff className="h-3 w-3" />
                Demo mode — offline data
              </Badge>
            )}

            {/* Filter Badge */}
            {activeFilterCount > 0 && (
              <Badge variant="default" className="flex items-center gap-1">
                <Filter className="h-3 w-3" />
                {activeFilterCount}
              </Badge>
            )}

            {/* Clear Button */}
            {query && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleClear}
                aria-label="Clear search"
                className="h-8 w-8"
              >
                <X className="h-4 w-4" />
              </Button>
            )}

            {/* Filter Toggle */}
            <Button
              variant="outline"
              size="icon"
              onClick={() => setShowFilters(!showFilters)}
              aria-label={showFilters ? "Hide filters" : "Show filters"}
              className={cn(
                "h-8 w-8",
                showFilters && "bg-primary text-primary-foreground"
              )}
            >
              {showFilters ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>

            {/* Search Button */}
            <Button
              onClick={handleSearch}
              disabled={isLoading || (!query && activeFilterCount === 0)}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
            >
              Search
            </Button>
          </div>
        </div>

        {/* Collapsible Filters Panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden border-t border-border/50"
            >
              <div className="p-4 space-y-4 bg-muted/30">
                {/* Category Filter */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Category
                  </label>
                  <select
                    value={filters.category || ''}
                    onChange={(e) => updateFilter('category', e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                  >
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat === 'All Categories' ? '' : cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Store Filter */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">
                      Store
                    </label>
                    <select
                      value={filters.store || ''}
                      onChange={(e) => updateFilter('store', e.target.value)}
                      className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                    >
                      {STORES.map((store) => (
                        <option key={store.value} value={store.value}>
                          {store.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Min Price */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">
                      Min Price
                    </label>
                    <Input
                      type="number"
                      placeholder="0"
                      value={filters.minPrice || ''}
                      onChange={(e) => updateFilter('minPrice', parseFloat(e.target.value))}
                      className="text-sm"
                    />
                  </div>

                  {/* Max Price */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">
                      Max Price
                    </label>
                    <Input
                      type="number"
                      placeholder="∞"
                      value={filters.maxPrice || ''}
                      onChange={(e) => updateFilter('maxPrice', parseFloat(e.target.value))}
                      className="text-sm"
                    />
                  </div>
                </div>

                {/* Sort Options */}
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Sort By
                  </label>
                  <select
                    value={`${filters.sortBy}-${filters.sortOrder}`}
                    onChange={(e) => handleSortChange(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm"
                  >
                    {SORT_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Filter Actions */}
                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleClear}
                    disabled={activeFilterCount === 0 && !query}
                  >
                    Clear All
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => {
                      handleSearch();
                      setShowFilters(false);
                    }}
                    className="bg-gradient-to-r from-blue-600 to-purple-600"
                  >
                    Apply Filters
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </div>
  );
};
