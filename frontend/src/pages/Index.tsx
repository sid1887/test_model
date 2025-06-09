import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, TrendingUp, Shield, Zap } from 'lucide-react';
import { FloatingSearch } from '@/components/ui/floating-search';
import { ValueScoredProductCard } from '@/components/ui/value-scored-product-card';
import { ComparisonMatrix } from '@/components/ui/comparison-matrix';
import { TrendChart } from '@/components/ui/trend-chart';
import { MagneticButton } from '@/components/ui/magnetic-button';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { PageTransition } from '@/components/ui/page-transition';
import { ScrollReveal } from '@/components/ui/scroll-reveal';
import { FloatingElements } from '@/components/ui/floating-elements';
import { ProductCardSkeleton } from '@/components/ui/skeleton-loader';
import { ResponsiveNavigation } from '@/components/ui/responsive-navigation';
import { SuspenseWrapper } from '@/components/ui/loading-system';
import { ScreenReaderAnnouncement } from '@/hooks/useAccessibility';
import { Product } from '@/types/product';

const Index = () => {
  const [likedProducts, setLikedProducts] = useState<Set<string>>(new Set());
  const [selectedProducts, setSelectedProducts] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [announcement, setAnnouncement] = useState('');
  const [showComparison, setShowComparison] = useState(false);

  // Enhanced navigation with smart features
  const navigationItems = [
    { label: 'Home', href: '/' },
    { label: 'AI Search', href: '/search' },
    { label: 'Price Alerts', href: '/alerts' },
    { label: 'Smart Lists', href: '/lists' },
    { label: 'Analytics', href: '/analytics' }
  ];

  // Enhanced mock product data with AI-powered insights
  const featuredProducts: Product[] = [
    {
      id: '1',
      name: 'iPhone 15 Pro Max - Titanium Edition',
      price: '$1,199',
      originalPrice: '$1,299',
      rating: 4.8,
      reviewCount: 2847,
      image: '/placeholder.svg',
      store: 'Apple Store',
      discount: '8% OFF',
      valueScore: 4.2,
      specs: ['8 GB RAM', '256 GB Storage', 'A17 Pro', 'ProRes Video', '120Hz Display'],
      priceChange: -2.5,
      chartData: [
        { date: '2024-05-01', actual: 1299, predicted: null },
        { date: '2024-05-15', actual: 1250, predicted: null },
        { date: '2024-06-01', actual: 1199, predicted: null },
        { date: '2024-06-08', actual: null, predicted: 1150 },
        { date: '2024-06-15', actual: null, predicted: 1120 }
      ]
    },
    {
      id: '2',
      name: 'MacBook Pro M3 - Space Black',
      price: '$1,999',
      originalPrice: '$2,199',
      rating: 4.9,
      reviewCount: 1523,
      image: '/placeholder.svg',
      store: 'Best Buy',
      discount: '9% OFF',
      valueScore: 4.7,
      specs: ['16 GB RAM', '512 GB SSD', 'M3 Pro', '18hr Battery', 'Liquid Retina XDR'],
      priceChange: 3.2,
      chartData: [
        { date: '2024-05-01', actual: 2199, predicted: null },
        { date: '2024-05-15', actual: 2100, predicted: null },
        { date: '2024-06-01', actual: 1999, predicted: null },
        { date: '2024-06-08', actual: null, predicted: 2050 },
        { date: '2024-06-15', actual: null, predicted: 2080 }
      ]
    },
    {
      id: '3',
      name: 'AirPods Pro 2nd Generation',
      price: '$229',
      originalPrice: '$249',
      rating: 4.7,
      reviewCount: 3421,
      image: '/placeholder.svg',
      store: 'Amazon',
      discount: '8% OFF',
      valueScore: 4.5,
      specs: ['Active Noise Cancel', '6hr Battery', 'H2 Chip', 'Spatial Audio', 'MagSafe'],
      priceChange: -1.8,
      chartData: [
        { date: '2024-05-01', actual: 249, predicted: null },
        { date: '2024-05-15', actual: 239, predicted: null },
        { date: '2024-06-01', actual: 229, predicted: null },
        { date: '2024-06-08', actual: null, predicted: 225 },
        { date: '2024-06-15', actual: null, predicted: 220 }
      ]
    }
  ];

  const handleLike = (productId: string) => {
    setLikedProducts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(productId)) {
        newSet.delete(productId);
        setAnnouncement('Product removed from wishlist');
      } else {
        newSet.add(productId);
        setAnnouncement('Product added to wishlist - we\'ll track price drops for you!');
      }
      return newSet;
    });
  };

  const handleQuickCompare = (productId: string) => {
    setSelectedProducts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(productId)) {
        newSet.delete(productId);
        setAnnouncement('Product removed from comparison');
      } else {
        if (newSet.size >= 4) {
          setAnnouncement('Maximum 4 products can be compared at once');
          return prev;
        }
        newSet.add(productId);
        setAnnouncement(`Product added to comparison (${newSet.size + 1}/4)`);
      }
      
      if (newSet.size >= 2) {
        setShowComparison(true);
      }
      
      return newSet;
    });
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
      description: "ML algorithms predict price drops up to 30 days ahead across 10,000+ stores with 94% accuracy"
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

  // ... keep existing code (logo definition)
  const logo = (
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
  );

  const selectedProductsData = featuredProducts.filter(p => selectedProducts.has(p.id));

  return (
    <PageTransition>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-black dark:to-purple-900 transition-all duration-700 relative overflow-hidden">
        {/* Screen reader announcements */}
        <ScreenReaderAnnouncement message={announcement} />
        
        {/* Enhanced Floating Background Elements */}
        <FloatingElements />
        
        {/* Enhanced Animated Background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div
            animate={{
              scale: [1, 1.3, 1],
              rotate: [0, 180, 360],
              opacity: [0.3, 0.6, 0.3],
            }}
            transition={{
              duration: 25,
              repeat: Infinity,
              ease: "linear"
            }}
            className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-br from-blue-400/30 to-purple-600/30 rounded-full blur-3xl"
          />
          <motion.div
            animate={{
              scale: [1.3, 1, 1.3],
              rotate: [360, 180, 0],
              opacity: [0.4, 0.7, 0.4],
            }}
            transition={{
              duration: 30,
              repeat: Infinity,
              ease: "linear"
            }}
            className="absolute -bottom-40 -left-40 w-[500px] h-[500px] bg-gradient-to-br from-green-400/30 to-blue-600/30 rounded-full blur-3xl"
          />
          <motion.div
            animate={{
              scale: [1, 1.1, 1],
              x: [0, 100, 0],
              y: [0, -50, 0],
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute top-1/2 left-1/2 w-72 h-72 bg-gradient-to-br from-pink-400/20 to-yellow-400/20 rounded-full blur-3xl"
          />
        </div>

        {/* Enhanced Responsive Navigation */}
        <ResponsiveNavigation
          items={navigationItems}
          logo={logo}
          actions={<ThemeToggle />}
        />

        {/* Enhanced Hero Section */}
        <section className="relative z-10 text-center py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-6xl mx-auto space-y-8 sm:space-y-12">
            <ScrollReveal direction="up" delay={0.2}>
              <motion.h2 
                className="text-4xl sm:text-6xl lg:text-8xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent leading-tight"
                animate={{
                  backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
                }}
                transition={{
                  duration: 5,
                  repeat: Infinity,
                  ease: "linear",
                }}
                style={{
                  backgroundSize: "200% 200%",
                }}
              >
                AI-Powered Shopping
                <br />
                <span className="text-2xl sm:text-4xl lg:text-6xl">Revolution</span>
              </motion.h2>
            </ScrollReveal>
            
            <ScrollReveal direction="up" delay={0.4}>
              <motion.p
                className="text-lg sm:text-xl lg:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed px-4"
                whileHover={{ scale: 1.02 }}
              >
                Experience next-generation e-commerce with GPT-4 powered discovery, predictive analytics, 
                blockchain-verified reviews, and personalized AI recommendations that save you time and money
              </motion.p>
            </ScrollReveal>

            <ScrollReveal direction="up" delay={0.6}>
              <motion.div
                whileHover={{ scale: 1.02 }}
                transition={{ type: "spring", stiffness: 300 }}
                className="px-4 relative z-20"
              >
                <FloatingSearch
                  onSearch={(query) => console.log('AI Search:', query)}
                  onImageSearch={() => console.log('Visual search activated')}
                  onVoiceSearch={() => console.log('Voice search activated')}
                />
                <div className="mt-2 text-xs text-muted-foreground flex items-center justify-center gap-1">
                  <span>⚡</span>
                  <span>0.03s avg. • AI-Enhanced</span>
                </div>
              </motion.div>
            </ScrollReveal>

            <ScrollReveal direction="up" delay={0.8}>
              <div className="flex flex-col sm:flex-row gap-4 sm:gap-6 justify-center items-center px-4">
                <MagneticButton 
                  onClick={() => console.log('Start AI shopping')}
                  className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg"
                >
                  Start AI Shopping
                </MagneticButton>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="w-full sm:w-auto"
                >
                  <button className="w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg font-semibold text-purple-600 dark:text-purple-400 border-2 border-purple-600/30 rounded-2xl backdrop-blur-md hover:bg-purple-600/10 transition-all duration-300">
                    Watch AI Demo
                  </button>
                </motion.div>
              </div>
            </ScrollReveal>
          </div>
        </section>

        {/* Enhanced Features Section */}
        <section className="relative z-10 py-16 sm:py-24 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <ScrollReveal direction="up">
              <motion.h3
                className="text-3xl sm:text-4xl lg:text-5xl font-bold text-center mb-12 sm:mb-20 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent px-4"
                whileHover={{ scale: 1.05 }}
              >
                Why 2M+ Smart Shoppers Choose Cumpair
              </motion.h3>
            </ScrollReveal>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
              {features.map((feature, index) => (
                <ScrollReveal key={feature.title} direction="up" delay={index * 0.1}>
                  <motion.div
                    className="backdrop-blur-xl bg-white/80 dark:bg-black/60 p-6 sm:p-8 rounded-3xl shadow-2xl border border-white/20 dark:border-white/10 group cursor-pointer h-full"
                    whileHover={{ 
                      y: -15, 
                      scale: 1.05,
                      boxShadow: "0 25px 50px rgba(0,0,0,0.15)"
                    }}
                    whileTap={{ scale: 0.98 }}
                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
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
                </ScrollReveal>
              ))}
            </div>
          </div>
        </section>

        {/* Enhanced Featured Products Section */}
        <section className="relative z-10 py-16 sm:py-24 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <ScrollReveal direction="up">
              <div className="text-center mb-12 sm:mb-20">
                <motion.h3 
                  className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4 sm:mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent px-4"
                  whileHover={{ scale: 1.05 }}
                >
                  AI-Curated Premium Selection
                </motion.h3>
                <motion.p 
                  className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto px-4"
                  whileHover={{ scale: 1.02 }}
                >
                  Discover hand-picked products with AI value scores, predictive pricing, and exclusive deals
                </motion.p>
              </div>
            </ScrollReveal>

            <SuspenseWrapper
              loadingType="skeleton"
              loadingMessage="Loading AI-curated products..."
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
                {isLoading ? (
                  Array.from({ length: 3 }).map((_, i) => (
                    <ScrollReveal key={i} direction="up" delay={i * 0.1}>
                      <ProductCardSkeleton />
                    </ScrollReveal>
                  ))
                ) : (
                  featuredProducts.map((product, index) => (
                    <ScrollReveal key={product.id} direction="up" delay={index * 0.1}>
                      <ValueScoredProductCard
                        {...product}
                        isLiked={likedProducts.has(product.id)}
                        isComparing={selectedProducts.has(product.id)}
                        onLike={handleLike}
                        onCompare={handleQuickCompare}
                        onAddToCart={(id) => {
                          console.log('Add to cart:', id);
                          setAnnouncement('Product added to cart with price protection');
                        }}
                      />
                    </ScrollReveal>
                  ))
                )}
              </div>
            </SuspenseWrapper>

            {selectedProducts.size >= 2 && (
              <ScrollReveal direction="up" delay={0.2}>
                <div className="text-center mt-12">
                  <MagneticButton
                    onClick={() => setShowComparison(!showComparison)}
                    className="px-8 sm:px-10 py-4 sm:py-5 text-base sm:text-lg"
                  >
                    {showComparison ? 'Hide' : 'Show'} AI Comparison ({selectedProducts.size})
                  </MagneticButton>
                </div>
              </ScrollReveal>
            )}

            {showComparison && selectedProductsData.length >= 2 && (
              <ScrollReveal direction="up" delay={0.3}>
                <div className="mt-16">
                  <ComparisonMatrix 
                    products={selectedProductsData}
                    onSave={() => console.log('Save comparison')}
                    onRemove={(id) => handleQuickCompare(id)}
                  />
                </div>
              </ScrollReveal>
            )}

            <ScrollReveal direction="up" delay={0.3}>
              <div className="text-center mt-12 sm:mt-16">
                <MagneticButton
                  onClick={() => console.log('Explore AI marketplace')}
                  className="px-8 sm:px-10 py-4 sm:py-5 text-base sm:text-lg"
                >
                  Explore AI Marketplace
                </MagneticButton>
              </div>
            </ScrollReveal>
          </div>
        </section>

        {/* Enhanced Trend Chart Section */}
        {selectedProductsData.length > 0 && (
          <section className="relative z-10 py-16 sm:py-24 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
              <ScrollReveal direction="up">
                <motion.h3 
                  className="text-3xl sm:text-4xl lg:text-5xl font-bold text-center mb-12 sm:mb-20 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent px-4"
                  whileHover={{ scale: 1.05 }}
                >
                  AI Price Prediction Analytics
                </motion.h3>
              </ScrollReveal>
              
              <ScrollReveal direction="up" delay={0.2}>
                <TrendChart products={selectedProductsData} />
              </ScrollReveal>
            </div>
          </section>
        )}

        {/* Enhanced CTA Section */}
        <section className="relative z-10 py-16 sm:py-24 px-4 sm:px-6 lg:px-8">
          <ScrollReveal direction="up">
            <motion.div
              className="max-w-5xl mx-auto text-center backdrop-blur-xl bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 p-8 sm:p-16 rounded-3xl border border-white/20 dark:border-white/10 shadow-2xl relative overflow-hidden"
              whileHover={{ scale: 1.02 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <motion.div
                className="absolute inset-0 opacity-10"
                animate={{
                  backgroundPosition: ["0% 0%", "100% 100%"],
                }}
                transition={{
                  duration: 10,
                  repeat: Infinity,
                  repeatType: "reverse",
                }}
                style={{
                  backgroundImage: "radial-gradient(circle, #3b82f6 1px, transparent 1px)",
                  backgroundSize: "50px 50px",
                }}
              />
              
              <motion.h3 
                className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6 sm:mb-8 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent relative z-10 px-4"
                whileHover={{ scale: 1.05 }}
              >
                Join the AI Shopping Revolution
              </motion.h3>
              <motion.p 
                className="text-lg sm:text-xl text-muted-foreground mb-8 sm:mb-12 max-w-3xl mx-auto leading-relaxed relative z-10 px-4"
                whileHover={{ scale: 1.02 }}
              >
                Join 2M+ intelligent shoppers saving $500+ annually with AI-powered insights, 
                predictive pricing, and personalized recommendations
              </motion.p>
              <div className="flex flex-col sm:flex-row gap-4 sm:gap-6 justify-center relative z-10 px-4">
                <MagneticButton
                  onClick={() => console.log('Start AI journey')}
                  className="w-full sm:w-auto px-8 sm:px-10 py-4 sm:py-5 text-base sm:text-lg"
                  strength={0.4}
                >
                  Start AI Journey Free
                </MagneticButton>
                <motion.button
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  className="w-full sm:w-auto px-8 sm:px-10 py-4 sm:py-5 text-base sm:text-lg font-semibold bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl hover:bg-white/20 transition-all duration-300"
                >
                  Schedule AI Demo
                </motion.button>
              </div>
            </motion.div>
          </ScrollReveal>
        </section>
      </div>
    </PageTransition>
  );
};

export default Index;
