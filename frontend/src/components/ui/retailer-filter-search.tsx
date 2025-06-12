import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Camera, Mic, Filter, Store, ChevronDown, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface RetailerFilterSearchProps {
  onSearch?: (query: string, filters: SearchFilters) => void;
  onImageSearch?: () => void;
  onVoiceSearch?: () => void;
  className?: string;
}

interface SearchFilters {
  category?: string;
  priority?: string;
  includeSpecialty?: boolean;
  maxRetailers?: number;
}

// Retailer data matching the backend categories
const RETAILER_CATEGORIES = {
  GENERAL: {
    name: 'General Merchandise',
    description: 'All-purpose retailers with diverse product catalogs',
    retailers: ['Amazon', 'Walmart', 'Target', 'eBay']
  },
  ELECTRONICS: {
    name: 'Electronics & Tech',
    description: 'Specialized in technology and electronic products',
    retailers: ['Best Buy', 'Newegg', 'B&H Photo']
  },
  FASHION: {
    name: 'Fashion & Apparel',
    description: 'Clothing, accessories, and fashion items',
    retailers: ['Macy\'s', 'Nordstrom', 'Zappos']
  },
  HOME_IMPROVEMENT: {
    name: 'Home & Garden',
    description: 'Home improvement, furniture, and garden supplies',
    retailers: ['Home Depot', 'Lowe\'s', 'Wayfair']
  },
  WHOLESALE: {
    name: 'Wholesale & Bulk',
    description: 'Bulk purchases and membership-based shopping',
    retailers: ['Costco']
  },
  SPECIALTY: {
    name: 'Specialty Online',
    description: 'Specialized online retailers with unique offerings',
    retailers: ['Overstock']
  }
};

const RETAILER_PRIORITIES = {
  HIGH: {
    name: 'High Priority',
    description: 'Major retailers with high traffic and reliability',
    badge: 'bg-green-500'
  },
  MEDIUM: {
    name: 'Medium Priority',
    description: 'Established retailers with good coverage',
    badge: 'bg-yellow-500'
  },
  LOW: {
    name: 'Low Priority',
    description: 'Specialized and niche retailers',
    badge: 'bg-gray-500'
  }
};

const RetailerFilterSearch: React.FC<RetailerFilterSearchProps> = ({
  onSearch,
  onImageSearch,
  onVoiceSearch,
  className
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({
    includeSpecialty: true,
    maxRetailers: 8
  });
  const [showFilters, setShowFilters] = useState(false);
  const [isAdvanced, setIsAdvanced] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const suggestions = [
    "iPhone 15 Pro Max",
    "MacBook Pro M3",
    "AirPods Pro 2",
    "Samsung Galaxy S24",
    "Sony WH-1000XM5",
    "Nintendo Switch OLED",
    "Tesla Model Y accessories",
    "Nike Air Jordan 1"
  ];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim() && onSearch) {
      onSearch(searchQuery, filters);
      setIsFocused(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setSearchQuery(suggestion);
    if (onSearch) {
      onSearch(suggestion, filters);
    }
    setIsFocused(false);
  };

  const updateFilter = (key: keyof SearchFilters, value: string | boolean | number) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      includeSpecialty: true,
      maxRetailers: 8
    });
  };

  const getActiveFiltersCount = () => {
    let count = 0;
    if (filters.category) count++;
    if (filters.priority) count++;
    if (!filters.includeSpecialty) count++;
    if (filters.maxRetailers !== 8) count++;
    return count;
  };

  const getSelectedRetailers = () => {
    if (!filters.category) return [];
    return RETAILER_CATEGORIES[filters.category as keyof typeof RETAILER_CATEGORIES]?.retailers || [];
  };

  return (
    <div className={cn("relative w-full max-w-4xl mx-auto", className)}>
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="relative z-30"
      >
        {/* Main Search Container */}
        <Card className={cn(
          "relative backdrop-blur-xl bg-white/95 dark:bg-black/90 shadow-2xl border border-white/20 dark:border-white/10 transition-all duration-300",
          isFocused && "ring-2 ring-blue-500/50 shadow-blue-500/25"
        )}>
          <div className="p-4">
            {/* Search Input Row */}
            <form onSubmit={handleSearch} className="flex items-center gap-3 mb-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => setIsFocused(true)}
                  onBlur={() => setTimeout(() => setIsFocused(false), 200)}
                  placeholder="Search across 15+ major retailers..."
                  className="pl-10 pr-4 h-12 text-lg border-0 bg-transparent focus:ring-0 focus:outline-none"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowFilters(!showFilters)}
                  className="relative"
                >
                  <Filter className="w-4 h-4 mr-2" />
                  Filters
                  {getActiveFiltersCount() > 0 && (
                    <Badge variant="secondary" className="ml-2 px-2 py-0 text-xs">
                      {getActiveFiltersCount()}
                    </Badge>
                  )}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={onImageSearch}
                  className="bg-gradient-to-br from-green-400 to-blue-500 text-white hover:from-green-500 hover:to-blue-600"
                >
                  <Camera className="w-4 h-4" />
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={onVoiceSearch}
                  className="bg-gradient-to-br from-purple-400 to-pink-500 text-white hover:from-purple-500 hover:to-pink-600"
                >
                  <Mic className="w-4 h-4" />
                </Button>

                <Button
                  type="submit"
                  className="px-6 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                >
                  Search
                </Button>
              </div>
            </form>

            {/* Filter Panel */}
            <AnimatePresence>
              {showFilters && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="border-t border-border pt-4"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Category Filter */}
                    <div>
                      <label className="text-sm font-medium mb-2 block">Retailer Category</label>
                      <Select
                        value={filters.category || ''}
                        onValueChange={(value) => updateFilter('category', value || '')}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="All Categories" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="">All Categories</SelectItem>
                          {Object.entries(RETAILER_CATEGORIES).map(([key, category]) => (
                            <SelectItem key={key} value={key}>
                              <div className="flex items-center gap-2">
                                <Store className="w-4 h-4" />
                                <div>
                                  <div className="font-medium">{category.name}</div>
                                  <div className="text-xs text-muted-foreground">{category.retailers.length} retailers</div>
                                </div>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Priority Filter */}
                    <div>
                      <label className="text-sm font-medium mb-2 block">Priority Level</label>
                      <Select
                        value={filters.priority || ''}
                        onValueChange={(value) => updateFilter('priority', value || '')}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="All Priorities" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="">All Priorities</SelectItem>
                          {Object.entries(RETAILER_PRIORITIES).map(([key, priority]) => (
                            <SelectItem key={key} value={key}>
                              <div className="flex items-center gap-2">
                                <div className={cn("w-3 h-3 rounded-full", priority.badge)}></div>
                                <span>{priority.name}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Max Retailers */}
                    <div>
                      <label className="text-sm font-medium mb-2 block">Max Retailers</label>
                      <Select
                        value={filters.maxRetailers?.toString() || '8'}
                        onValueChange={(value) => updateFilter('maxRetailers', parseInt(value))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="4">4 retailers</SelectItem>
                          <SelectItem value="8">8 retailers</SelectItem>
                          <SelectItem value="12">12 retailers</SelectItem>
                          <SelectItem value="15">All 15 retailers</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Specialty Toggle */}
                    <div>
                      <label className="text-sm font-medium mb-2 block">Options</label>
                      <div className="space-y-2">
                        <label className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={filters.includeSpecialty}
                            onChange={(e) => updateFilter('includeSpecialty', e.target.checked)}
                            className="rounded border-gray-300"
                          />
                          Include specialty retailers
                        </label>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={clearFilters}
                          className="text-xs h-auto p-1"
                        >
                          Clear filters
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Selected Category Preview */}
                  {filters.category && (
                    <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                      <div className="text-sm font-medium mb-2">
                        Selected: {RETAILER_CATEGORIES[filters.category as keyof typeof RETAILER_CATEGORIES]?.name}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {getSelectedRetailers().map((retailer) => (
                          <Badge key={retailer} variant="secondary" className="text-xs">
                            {retailer}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </Card>

        {/* Search Suggestions */}
        <AnimatePresence>
          {isFocused && (
            <>
              {/* Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-10"
                onClick={() => setIsFocused(false)}
              />
              
              {/* Suggestions Panel */}
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="absolute top-full left-0 right-0 mt-2 backdrop-blur-xl bg-white/95 dark:bg-black/90 rounded-xl shadow-2xl border border-white/20 dark:border-white/10 overflow-hidden z-50"
              >
                <div className="p-4">
                  <div className="text-xs font-medium text-muted-foreground mb-3">Popular Searches</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {suggestions.map((suggestion, index) => (
                      <motion.button
                        key={suggestion}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-accent transition-colors duration-200 flex items-center gap-3"
                      >
                        <Search className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        <span className="text-sm">{suggestion}</span>
                      </motion.button>
                    ))}
                  </div>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export { RetailerFilterSearch };
export type { SearchFilters };
