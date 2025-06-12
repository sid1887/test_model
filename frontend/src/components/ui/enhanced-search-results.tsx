import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Filter, Star, ExternalLink, ShoppingCart, Heart, GitCompare, SortAsc, Store, TrendingUp, Clock } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';

interface SearchResult {
  id: string;
  title: string;
  price: string;
  originalPrice?: string;
  image?: string;
  link: string;
  site: string;
  rating?: number;
  reviewCount?: number;
  retailer_info?: {
    name: string;
    category: string;
    priority: string;
    base_url: string;
  };
  features?: string[];
  availability?: 'in-stock' | 'limited' | 'out-of-stock';
  shipping?: {
    type: string;
    cost: number;
    days: number;
  };
}

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  loading?: boolean;
  onAddToCart?: (result: SearchResult) => void;
  onAddToWishlist?: (result: SearchResult) => void;
  onCompare?: (result: SearchResult) => void;
  onRetailerFilter?: (retailers: string[]) => void;
  className?: string;
}

interface FilterState {
  retailers: string[];
  categories: string[];
  priorities: string[];
  priceRange: [number, number];
  rating: number;
  sortBy: 'price' | 'rating' | 'retailer' | 'relevance';
  sortOrder: 'asc' | 'desc';
}

const RETAILER_CATEGORIES = {
  GENERAL: { name: 'General', color: 'bg-blue-500' },
  ELECTRONICS: { name: 'Electronics', color: 'bg-purple-500' },
  FASHION: { name: 'Fashion', color: 'bg-pink-500' },
  HOME_IMPROVEMENT: { name: 'Home & Garden', color: 'bg-green-500' },
  WHOLESALE: { name: 'Wholesale', color: 'bg-orange-500' },
  SPECIALTY: { name: 'Specialty', color: 'bg-gray-500' }
};

const PRIORITY_LEVELS = {
  HIGH: { name: 'High Priority', color: 'bg-green-500' },
  MEDIUM: { name: 'Medium Priority', color: 'bg-yellow-500' },
  LOW: { name: 'Low Priority', color: 'bg-gray-500' }
};

const EnhancedSearchResults: React.FC<SearchResultsProps> = ({
  results,
  query,
  loading = false,
  onAddToCart,
  onAddToWishlist,
  onCompare,
  onRetailerFilter,
  className
}) => {
  const [filters, setFilters] = useState<FilterState>({
    retailers: [],
    categories: [],
    priorities: [],
    priceRange: [0, 1000],
    rating: 0,
    sortBy: 'relevance',
    sortOrder: 'desc'
  });
  const [showFilters, setShowFilters] = useState(false);
  const [comparedItems, setComparedItems] = useState<Set<string>>(new Set());
  const [wishlistItems, setWishlistItems] = useState<Set<string>>(new Set());

  // Get unique retailers from results
  const availableRetailers = Array.from(
    new Set(results.map(r => r.site || r.retailer_info?.name || 'Unknown'))
  );

  // Get unique categories from results
  const availableCategories = Array.from(
    new Set(results.map(r => r.retailer_info?.category).filter(Boolean))
  );

  // Get unique priorities from results
  const availablePriorities = Array.from(
    new Set(results.map(r => r.retailer_info?.priority).filter(Boolean))
  );

  // Filter and sort results
  const filteredResults = results.filter(result => {
    // Retailer filter
    if (filters.retailers.length > 0) {
      const retailerName = result.site || result.retailer_info?.name || 'Unknown';
      if (!filters.retailers.includes(retailerName)) return false;
    }

    // Category filter
    if (filters.categories.length > 0) {
      if (!result.retailer_info?.category || !filters.categories.includes(result.retailer_info.category)) {
        return false;
      }
    }

    // Priority filter
    if (filters.priorities.length > 0) {
      if (!result.retailer_info?.priority || !filters.priorities.includes(result.retailer_info.priority)) {
        return false;
      }
    }

    // Price filter
    const price = parseFloat(result.price.replace(/[^0-9.]/g, '')) || 0;
    if (price < filters.priceRange[0] || price > filters.priceRange[1]) return false;

    // Rating filter
    if (filters.rating > 0 && (!result.rating || result.rating < filters.rating)) return false;

    return true;
  });
  const sortedResults = [...filteredResults].sort((a, b) => {
    let comparison = 0;

    switch (filters.sortBy) {
      case 'price': {
        const priceA = parseFloat(a.price.replace(/[^0-9.]/g, '')) || 0;
        const priceB = parseFloat(b.price.replace(/[^0-9.]/g, '')) || 0;
        comparison = priceA - priceB;
        break;
      }
      case 'rating':
        comparison = (b.rating || 0) - (a.rating || 0);
        break;
      case 'retailer': {
        const retailerA = a.site || a.retailer_info?.name || '';
        const retailerB = b.site || b.retailer_info?.name || '';
        comparison = retailerA.localeCompare(retailerB);
        break;
      }
      case 'relevance':
      default:
        // Keep original order for relevance
        return 0;
    }

    return filters.sortOrder === 'asc' ? comparison : -comparison;
  });
  const updateFilter = (key: keyof FilterState, value: string | string[] | number) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const toggleRetailerFilter = (retailer: string) => {
    const newRetailers = filters.retailers.includes(retailer)
      ? filters.retailers.filter(r => r !== retailer)
      : [...filters.retailers, retailer];
    
    updateFilter('retailers', newRetailers);
    onRetailerFilter?.(newRetailers);
  };

  const toggleCompare = (result: SearchResult) => {
    const newCompared = new Set(comparedItems);
    if (newCompared.has(result.id)) {
      newCompared.delete(result.id);
    } else if (newCompared.size < 4) {
      newCompared.add(result.id);
    }
    setComparedItems(newCompared);
    onCompare?.(result);
  };

  const toggleWishlist = (result: SearchResult) => {
    const newWishlist = new Set(wishlistItems);
    if (newWishlist.has(result.id)) {
      newWishlist.delete(result.id);
    } else {
      newWishlist.add(result.id);
    }
    setWishlistItems(newWishlist);
    onAddToWishlist?.(result);
  };

  const getRetailerBadgeColor = (category?: string, priority?: string) => {
    if (category && RETAILER_CATEGORIES[category as keyof typeof RETAILER_CATEGORIES]) {
      return RETAILER_CATEGORIES[category as keyof typeof RETAILER_CATEGORIES].color;
    }
    if (priority && PRIORITY_LEVELS[priority as keyof typeof PRIORITY_LEVELS]) {
      return PRIORITY_LEVELS[priority as keyof typeof PRIORITY_LEVELS].color;
    }
    return 'bg-gray-500';
  };

  const getAvailabilityIcon = (availability?: string) => {
    switch (availability) {
      case 'in-stock':
        return <div className="w-2 h-2 bg-green-500 rounded-full" />;
      case 'limited':
        return <div className="w-2 h-2 bg-yellow-500 rounded-full" />;
      case 'out-of-stock':
        return <div className="w-2 h-2 bg-red-500 rounded-full" />;
      default:
        return <div className="w-2 h-2 bg-gray-400 rounded-full" />;
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} className="p-6">
            <div className="animate-pulse flex space-x-4">
              <div className="rounded w-24 h-24 bg-gray-300"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                <div className="h-4 bg-gray-300 rounded w-1/2"></div>
                <div className="h-4 bg-gray-300 rounded w-1/4"></div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header with filters */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">
            Search Results for "{query}"
          </h2>
          <p className="text-muted-foreground">
            Found {sortedResults.length} products across {availableRetailers.length} retailers
          </p>
        </div>

        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            Filters
            {(filters.retailers.length + filters.categories.length + filters.priorities.length) > 0 && (
              <Badge variant="secondary" className="ml-2">
                {filters.retailers.length + filters.categories.length + filters.priorities.length}
              </Badge>
            )}
          </Button>

          <Select value={filters.sortBy} onValueChange={(value) => updateFilter('sortBy', value)}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="relevance">Relevance</SelectItem>
              <SelectItem value="price">Price</SelectItem>
              <SelectItem value="rating">Rating</SelectItem>
              <SelectItem value="retailer">Retailer</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Filter Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Retailer Filter */}
                <div>
                  <h3 className="font-semibold mb-3">Retailers</h3>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {availableRetailers.map(retailer => (
                      <label key={retailer} className="flex items-center space-x-2">
                        <Checkbox
                          checked={filters.retailers.includes(retailer)}
                          onCheckedChange={() => toggleRetailerFilter(retailer)}
                        />
                        <span className="text-sm">{retailer}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Category Filter */}
                <div>
                  <h3 className="font-semibold mb-3">Categories</h3>
                  <div className="space-y-2">                    {availableCategories.map(category => category && (
                      <label key={category} className="flex items-center space-x-2">
                        <Checkbox
                          checked={filters.categories.includes(category)}
                          onCheckedChange={() => {
                            const newCategories = filters.categories.includes(category)
                              ? filters.categories.filter(c => c !== category)
                              : [...filters.categories, category];
                            updateFilter('categories', newCategories);
                          }}
                        />
                        <span className="text-sm">
                          {RETAILER_CATEGORIES[category as keyof typeof RETAILER_CATEGORIES]?.name || category}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Priority Filter */}
                <div>
                  <h3 className="font-semibold mb-3">Priority</h3>
                  <div className="space-y-2">                    {availablePriorities.map(priority => priority && (
                      <label key={priority} className="flex items-center space-x-2">
                        <Checkbox
                          checked={filters.priorities.includes(priority)}
                          onCheckedChange={() => {
                            const newPriorities = filters.priorities.includes(priority)
                              ? filters.priorities.filter(p => p !== priority)
                              : [...filters.priorities, priority];
                            updateFilter('priorities', newPriorities);
                          }}
                        />
                        <div className="flex items-center gap-2">
                          <div className={cn("w-3 h-3 rounded-full", 
                            PRIORITY_LEVELS[priority as keyof typeof PRIORITY_LEVELS]?.color || 'bg-gray-500'
                          )} />
                          <span className="text-sm">
                            {PRIORITY_LEVELS[priority as keyof typeof PRIORITY_LEVELS]?.name || priority}
                          </span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Rating Filter */}
                <div>
                  <h3 className="font-semibold mb-3">Minimum Rating</h3>
                  <Select 
                    value={filters.rating.toString()} 
                    onValueChange={(value) => updateFilter('rating', parseFloat(value))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">Any Rating</SelectItem>
                      <SelectItem value="3">3+ Stars</SelectItem>
                      <SelectItem value="4">4+ Stars</SelectItem>
                      <SelectItem value="4.5">4.5+ Stars</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedResults.map((result, index) => (
          <motion.div
            key={result.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="overflow-hidden hover:shadow-lg transition-all duration-300 h-full">
              {/* Image */}
              {result.image && (
                <div className="relative aspect-square bg-gray-100">
                  <img
                    src={result.image}
                    alt={result.title}
                    className="w-full h-full object-cover"
                  />
                  {/* Wishlist Button */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleWishlist(result)}
                    className="absolute top-2 right-2 p-2 bg-white/80 hover:bg-white"
                  >
                    <Heart 
                      className={cn("w-4 h-4", 
                        wishlistItems.has(result.id) ? "text-red-500 fill-current" : "text-gray-600"
                      )} 
                    />
                  </Button>
                </div>
              )}

              <div className="p-4 space-y-3">
                {/* Retailer Info */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge 
                      className={cn("text-white text-xs", 
                        getRetailerBadgeColor(result.retailer_info?.category, result.retailer_info?.priority)
                      )}
                    >
                      <Store className="w-3 h-3 mr-1" />
                      {result.retailer_info?.name || result.site}
                    </Badge>
                    {getAvailabilityIcon(result.availability)}
                  </div>
                  
                  {result.rating && (
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4 text-yellow-500 fill-current" />
                      <span className="text-sm font-medium">{result.rating}</span>
                      {result.reviewCount && (
                        <span className="text-xs text-muted-foreground">({result.reviewCount})</span>
                      )}
                    </div>
                  )}
                </div>

                {/* Title */}
                <h3 className="font-semibold text-lg line-clamp-2 leading-tight">
                  {result.title}
                </h3>

                {/* Price */}
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold text-green-600">
                    {result.price}
                  </span>
                  {result.originalPrice && (
                    <span className="text-sm text-muted-foreground line-through">
                      {result.originalPrice}
                    </span>
                  )}
                </div>

                {/* Shipping Info */}
                {result.shipping && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    <span>
                      {result.shipping.type} - {result.shipping.days} days
                      {result.shipping.cost > 0 && ` (+$${result.shipping.cost})`}
                    </span>
                  </div>
                )}

                {/* Features */}
                {result.features && result.features.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {result.features.slice(0, 3).map((feature, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                    {result.features.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{result.features.length - 3} more
                      </Badge>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button
                    onClick={() => onAddToCart?.(result)}
                    className="flex-1"
                    size="sm"
                  >
                    <ShoppingCart className="w-4 h-4 mr-2" />
                    Add to Cart
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toggleCompare(result)}
                    disabled={!comparedItems.has(result.id) && comparedItems.size >= 4}
                    className={cn(
                      comparedItems.has(result.id) && "bg-blue-50 border-blue-200"
                    )}
                  >
                    <GitCompare className="w-4 h-4" />
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(result.link, '_blank')}
                  >
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Comparison Panel */}
      {comparedItems.size > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-4 right-4 z-50"
        >
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <GitCompare className="w-5 h-5" />
              <span className="font-medium">
                {comparedItems.size} items to compare
              </span>
              <Button size="sm">
                Compare Now
              </Button>
            </div>
          </Card>
        </motion.div>
      )}

      {/* No Results */}
      {sortedResults.length === 0 && !loading && (
        <Card className="p-12 text-center">
          <Store className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-xl font-semibold mb-2">No products found</h3>
          <p className="text-muted-foreground mb-4">
            Try adjusting your filters or search terms
          </p>
          <Button 
            onClick={() => setFilters({
              retailers: [],
              categories: [],
              priorities: [],
              priceRange: [0, 1000],
              rating: 0,
              sortBy: 'relevance',
              sortOrder: 'desc'
            })}
          >
            Clear All Filters
          </Button>
        </Card>
      )}
    </div>
  );
};

export { EnhancedSearchResults };
export type { SearchResult, FilterState };
