import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, TrendingUp, Shield, Zap, Store, Settings } from 'lucide-react';
import { RetailerFilterSearch, SearchFilters } from '@/components/ui/retailer-filter-search';
import { EnhancedSearchResults, SearchResult } from '@/components/ui/enhanced-search-results';
import { RetailerDashboard } from '@/components/ui/retailer-dashboard';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// Simple Product type definition
interface Product {
  id: string;
  name: string;
  price: string;
  originalPrice?: string;
  rating: number;
  reviewCount: number;
  image: string;
  store: string;
  discount?: string;
  valueScore: number;
  specs: string[];
  priceChange: number;
  chartData: Array<{
    date: string;
    actual: number | null;
    predicted: number | null;
  }>;
}

const EnhancedIndex = () => {
  const [likedProducts, setLikedProducts] = useState<Set<string>>(new Set());
  const [selectedProducts, setSelectedProducts] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [announcement, setAnnouncement] = useState('');
  const [showComparison, setShowComparison] = useState(false);
  const [showRetailerDashboard, setShowRetailerDashboard] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [searchLoading, setSearchLoading] = useState(false);

  // Enhanced search handlers for 15+ retailers
  const handleEnhancedSearch = async (query: string, filters: SearchFilters) => {
    setSearchLoading(true);
    setCurrentQuery(query);
    setAnnouncement(`Searching across ${filters.maxRetailers || 8} retailers for "${query}"`);
    
    try {
      // Call enhanced search API with retailer filters
      const response = await fetch('/api/v1/enhanced-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          category: filters.category,
          priority: filters.priority,
          include_specialty: filters.includeSpecialty,
          max_retailers: filters.maxRetailers
        })
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`);
      }

      const data = await response.json();
      
      // Transform API results to SearchResult format
      const transformedResults: SearchResult[] = data.results.map((result: Record<string, unknown>, index: number) => ({
        id: `${result.site}-${index}`,
        title: result.title || result.name || 'Unknown Product',
        price: result.price_text || result.price || '$0.00',
        originalPrice: result.original_price as string,
        image: result.image_url || result.image as string,
        link: result.url || result.link || '#',
        site: result.site as string,
        rating: result.rating as number,
        reviewCount: result.review_count as number,
        retailer_info: result.retailer_info as {
          name: string;
          category: string;
          priority: string;
          base_url: string;
        },
        features: result.features as string[] || [],
        availability: result.availability as 'in-stock' | 'limited' | 'out-of-stock' || 'in-stock',
        shipping: result.shipping as {
          type: string;
          cost: number;
          days: number;
        }
      }));

      setSearchResults(transformedResults);
      setAnnouncement(`Found ${transformedResults.length} products across ${data.search_metadata?.retailers_searched || 0} retailers`);
      
    } catch (error) {
      console.error('Enhanced search failed:', error);
      setAnnouncement('Search failed - please try again');
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleImageSearch = () => {
    setAnnouncement('Visual search activated - upload an image to find similar products');
    // Image search functionality would be implemented here
  };

  const handleVoiceSearch = () => {
    setAnnouncement('Voice search activated - speak your search query');
    // Voice search functionality would be implemented here
  };

  const handleRetailerToggle = (retailerKey: string, status: string) => {
    setAnnouncement(`${retailerKey} retailer ${status === 'active' ? 'enabled' : 'disabled'}`);
    // API call to update retailer status would be implemented here
  };

  const handleRetailerConfig = (retailerKey: string) => {
    setAnnouncement(`Opening configuration for ${retailerKey}`);
    // Navigate to retailer configuration would be implemented here
  };

  const handleSearchResultAction = (action: string, result: SearchResult) => {
    switch (action) {
      case 'cart':
        setAnnouncement(`${result.title} added to cart with price protection`);
        break;
      case 'wishlist':
        setAnnouncement(`${result.title} added to wishlist - we'll track price drops`);
        break;
      case 'compare':
        setAnnouncement(`${result.title} added to comparison`);
        break;
    }
  };

  // Enhanced features with AI insights
  const features = [
    {
      icon: Sparkles,
      title: "AI-Powered Discovery",
      description: "Find products using natural language, images, or voice with GPT-4 powered search that understands context and intent"
    },
    {
      icon: TrendingUp,
      title: "Predictive Price Intelligence",
      description: "ML algorithms predict price drops up to 30 days ahead across 15+ stores with 94% accuracy"
    },
    {
      icon: Shield,
      title: "Trust Score & Verification",
      description: "Blockchain-verified reviews with AI sentiment analysis and fake review detection for authentic insights"
    },
    {
      icon: Zap,
      title: "Instant Smart Matching",
      description: "Sub-100ms product matching with personalized recommendations based on your shopping DNA"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-black dark:to-purple-900 transition-all duration-700 relative overflow-hidden">
      {/* Screen reader announcements */}
      {announcement && (
        <div className="sr-only" role="status" aria-live="polite">
          {announcement}
        </div>
      )}
      
      {/* Enhanced Floating Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            x: [0, 100, 0],
            y: [0, -100, 0],
            rotate: [0, 180, 360],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear",
          }}
          className="absolute top-1/4 left-1/4 w-64 h-64 bg-gradient-to-br from-blue-400/10 to-purple-400/10 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            x: [0, -120, 0],
            y: [0, 120, 0],
            rotate: [360, 180, 0],
          }}
          transition={{
            duration: 25,
            repeat: Infinity,
            ease: "linear",
          }}
          className="absolute top-1/2 left-1/2 w-72 h-72 bg-gradient-to-br from-pink-400/20 to-yellow-400/20 rounded-full blur-3xl"
        />
      </div>

      {/* Navigation */}
      <nav className="relative bg-background/95 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <motion.div
              className="flex items-center gap-3"
              whileHover={{ scale: 1.05 }}
            >
              <motion.div 
                className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg"
                whileHover={{ rotate: 180 }}
                transition={{ duration: 0.6 }}
              >
                <Sparkles className="w-6 h-6 text-white" />
              </motion.div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                Cumpair
              </h1>
            </motion.div>

            {/* Navigation Actions */}
            <div className="flex items-center gap-4">
              <Button
                variant="outline"
                onClick={() => setShowRetailerDashboard(!showRetailerDashboard)}
              >
                <Store className="w-4 h-4 mr-2" />
                Retailers
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10">
        {/* Hero Section */}
        <section className="py-16 sm:py-24 px-4 sm:px-6 lg:px-8">
          <div className="max-w-6xl mx-auto text-center space-y-8 sm:space-y-12">
            <motion.h2 
              className="text-4xl sm:text-6xl lg:text-8xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent leading-tight"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              AI-Powered Shopping
              <br />
              <span className="text-2xl sm:text-4xl lg:text-6xl">Revolution</span>
            </motion.h2>
            
            <motion.p
              className="text-lg sm:text-xl lg:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed px-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              Experience next-generation e-commerce with GPT-4 powered discovery, predictive analytics, 
              and personalized AI recommendations across 15+ major retailers
            </motion.p>

            <motion.div
              className="px-4 relative z-20"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              <RetailerFilterSearch
                onSearch={handleEnhancedSearch}
                onImageSearch={handleImageSearch}
                onVoiceSearch={handleVoiceSearch}
              />
              <div className="mt-4 text-center">
                <div className="text-xs text-muted-foreground flex items-center justify-center gap-1 mb-2">
                  <span>⚡</span>
                  <span>0.03s avg. • AI-Enhanced • 15+ Retailers</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowRetailerDashboard(!showRetailerDashboard)}
                  className="text-xs"
                >
                  <Store className="w-3 h-3 mr-1" />
                  {showRetailerDashboard ? 'Hide' : 'Manage'} Retailers
                </Button>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Retailer Dashboard */}
        {showRetailerDashboard && (
          <section className="py-16 px-4 sm:px-6 lg:px-8 bg-muted/50">
            <div className="max-w-7xl mx-auto">
              <RetailerDashboard
                onRetailerToggle={handleRetailerToggle}
                onRetailerConfig={handleRetailerConfig}
              />
            </div>
          </section>
        )}

        {/* Search Results */}
        {(searchResults.length > 0 || searchLoading) && (
          <section className="py-16 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
              <EnhancedSearchResults
                results={searchResults}
                query={currentQuery}
                loading={searchLoading}
                onAddToCart={(result) => handleSearchResultAction('cart', result)}
                onAddToWishlist={(result) => handleSearchResultAction('wishlist', result)}
                onCompare={(result) => handleSearchResultAction('compare', result)}
              />
            </div>
          </section>
        )}

        {/* Features Section */}
        <section className="relative z-10 py-16 sm:py-24 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <motion.h3 
              className="text-3xl sm:text-4xl lg:text-5xl font-bold text-center mb-12 sm:mb-20 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent px-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              Why 2M+ Smart Shoppers Choose Cumpair
            </motion.h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.title}
                  className="backdrop-blur-xl bg-white/80 dark:bg-black/60 p-6 sm:p-8 rounded-3xl shadow-2xl border border-white/20 dark:border-white/10 group cursor-pointer h-full"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: index * 0.1 }}
                  whileHover={{ 
                    y: -15, 
                    scale: 1.05,
                    boxShadow: "0 25px 50px rgba(0,0,0,0.15)"
                  }}
                  whileTap={{ scale: 0.98 }}
                >
                  <motion.div 
                    className="w-14 h-14 sm:w-16 sm:h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4 sm:mb-6 mx-auto shadow-lg"
                    whileHover={{ rotate: 360, scale: 1.1 }}
                    transition={{ duration: 0.6 }}
                  >
                    <feature.icon className="w-6 h-6 sm:w-8 sm:h-8 text-white" />
                  </motion.div>
                  <h4 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4 text-center group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors duration-300">
                    {feature.title}
                  </h4>
                  <p className="text-sm sm:text-base text-muted-foreground text-center leading-relaxed">
                    {feature.description}
                  </p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Enhanced CTA Section */}
        <section className="relative z-10 py-16 sm:py-24 px-4 sm:px-6 lg:px-8">
          <motion.div
            className="max-w-5xl mx-auto text-center backdrop-blur-xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 p-8 sm:p-16 rounded-3xl border border-white/20 dark:border-white/10 shadow-2xl relative overflow-hidden"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            whileHover={{ scale: 1.02 }}
          >
            <motion.h3 
              className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent px-4"
              whileHover={{ scale: 1.05 }}
            >
              Ready to Transform Your Shopping Experience?
            </motion.h3>
            <motion.p 
              className="text-lg sm:text-xl text-muted-foreground max-w-3xl mx-auto mb-8 sm:mb-12 px-4"
              whileHover={{ scale: 1.02 }}
            >
              Join 2M+ intelligent shoppers saving $500+ annually with AI-powered insights, 
              predictive pricing, and personalized recommendations across 15+ retailers
            </motion.p>
            <div className="flex flex-col sm:flex-row gap-4 sm:gap-6 justify-center relative z-10 px-4">
              <Button
                size="lg"
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold px-8 py-4"
                onClick={() => setAnnouncement('Welcome to Cumpair! Start exploring our AI-powered features.')}
              >
                Start AI Journey Free
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="font-semibold px-8 py-4"
              >
                Watch Demo
              </Button>
            </div>
          </motion.div>
        </section>
      </main>
    </div>
  );
};

export default EnhancedIndex;
