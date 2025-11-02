/**
 * Enhanced Analytics Page with Aether Design System
 * Beautiful UI with animations, glass morphism, and live data
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  TrendingUp, 
  BarChart3, 
  Brain, 
  DollarSign, 
  ArrowUp,
  ArrowDown,
  Zap,
  Activity
} from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';
import { AnalyticsOverview } from '../types/alerts';
import { TrendExplorer } from '../components/analytics/TrendExplorer';
import { ForecastDisplay } from '../components/analytics/ForecastDisplay';
import { SentimentPanel } from '../components/analytics/SentimentPanel';
import { RetailerComparison } from '../components/analytics/RetailerComparison';
import { AetherCard, AetherButton } from '@/components/angel';
import { ParticleField, MorphingShape, FloatingCard } from '@/components/animations';

export const AnalyticsPageEnhanced: React.FC = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  type TabId = 'trends' | 'forecast' | 'sentiment' | 'retailers';
  const [activeTab, setActiveTab] = useState<TabId>('trends');
  const [selectedProductId, setSelectedProductId] = useState<number>(1);
  const { getOverview, loading } = useAnalytics();

  const loadOverview = useCallback(async () => {
    const data = await getOverview();
    if (data) setOverview(data);
  }, [getOverview]);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  const tabs: Array<{ id: TabId; label: string; icon: React.ComponentType<{ className?: string }>; color: string }> = [
    { id: 'trends', label: 'Price Trends', icon: TrendingUp, color: 'blue' },
    { id: 'forecast', label: 'Forecast', icon: Brain, color: 'purple' },
    { id: 'sentiment', label: 'Sentiment', icon: Activity, color: 'green' },
    { id: 'retailers', label: 'Retailers', icon: DollarSign, color: 'yellow' }
  ];

  return (
    <div className="min-h-screen relative">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <ParticleField count={30} speed={0.3} />
        <div className="absolute top-20 right-20">
          <MorphingShape size={300} blur={60} />
        </div>
        <div className="absolute bottom-40 left-20">
          <MorphingShape size={250} blur={50} colors={['#10b981', '#3b82f6']} />
        </div>
      </div>

      <div className="relative z-10 p-6 max-w-7xl mx-auto">
        {/* Hero Header */}
        <motion.div
          className="mb-12"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="flex items-center justify-between flex-wrap gap-6">
            <div>
              <motion.div
                className="flex items-center gap-3 mb-2"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="p-3 rounded-2xl bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg">
                  <BarChart3 className="h-7 w-7" />
                </div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 
                               bg-clip-text text-transparent">
                  Analytics & Insights
                </h1>
              </motion.div>
              <motion.p
                className="text-gray-600 dark:text-gray-400 text-lg ml-16"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
                Track trends, forecasts, and market intelligence
              </motion.p>
            </div>

            {/* Product Selector */}
            <motion.div
              className="flex items-center gap-3"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 }}
            >
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Product ID:
              </span>
              <input
                type="number"
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(parseInt(e.target.value) || 1)}
                className="w-32 px-4 py-2 rounded-xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm
                         border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-blue-500 
                         focus:border-transparent transition-all"
                min="1"
              />
            </motion.div>
          </div>
        </motion.div>

        {/* Stats Grid */}
        {overview && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {[
              {
                icon: BarChart3,
                label: 'Products Tracked',
                value: overview.total_products,
                color: 'blue',
                gradient: 'from-blue-500 to-cyan-500'
              },
              {
                icon: (overview.avg_price_change ?? 0) >= 0 ? ArrowUp : ArrowDown,
                label: 'Avg. Price Change',
                value: `${(overview.avg_price_change ?? 0) >= 0 ? '+' : ''}${(overview.avg_price_change ?? 0).toFixed(1)}%`,
                color: (overview.avg_price_change ?? 0) >= 0 ? 'red' : 'green',
                gradient: (overview.avg_price_change ?? 0) >= 0 ? 'from-red-500 to-orange-500' : 'from-green-500 to-emerald-500'
              },
              {
                icon: DollarSign,
                label: 'Total Savings',
                value: `$${(overview.total_savings ?? 0).toFixed(2)}`,
                color: 'yellow',
                gradient: 'from-yellow-500 to-amber-500'
              },
              {
                icon: Brain,
                label: 'Forecasts Generated',
                value: overview.forecasts_generated || 0,
                color: 'purple',
                gradient: 'from-purple-500 to-pink-500'
              }
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index }}
              >
                <FloatingCard>
                  <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className={`p-3 rounded-xl bg-gradient-to-r ${stat.gradient} text-white shadow-lg`}>
                        <stat.icon className="h-6 w-6" />
                      </div>
                      <motion.div
                        className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 
                                   dark:from-white dark:to-gray-300 bg-clip-text text-transparent"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.3 + index * 0.1, type: 'spring' }}
                      >
                        {stat.value}
                      </motion.div>
                    </div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                      {stat.label}
                    </p>
                  </div>
                </FloatingCard>
              </motion.div>
            ))}
          </div>
        )}

        {/* Tab Navigation */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <AetherCard className="p-2">
            <div className="flex gap-2 flex-wrap">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <motion.button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex-1 min-w-[140px] px-6 py-4 rounded-xl font-medium transition-all duration-300
                      flex items-center justify-center gap-2 relative overflow-hidden
                      ${isActive 
                        ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg' 
                        : 'text-gray-700 dark:text-gray-300 hover:bg-white/50 dark:hover:bg-gray-800/50'
                      }
                    `}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {isActive && (
                      <motion.div
                        className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent"
                        animate={{
                          x: ['-100%', '100%']
                        }}
                        transition={{
                          duration: 1.5,
                          repeat: Infinity,
                          ease: 'easeInOut'
                        }}
                      />
                    )}
                    <Icon className="h-5 w-5" />
                    <span className="relative z-10">{tab.label}</span>
                  </motion.button>
                );
              })}
            </div>
          </AetherCard>
        </motion.div>

        {/* Content Area */}
        <AnimatePresence mode="wait">
          {loading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex justify-center items-center py-20"
            >
              <AetherCard className="p-12">
                <div className="flex flex-col items-center gap-4">
                  <motion.div
                    className="w-16 h-16 rounded-full border-4 border-blue-500/20 border-t-blue-500"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                  <p className="text-gray-600 dark:text-gray-400">Loading analytics...</p>
                </div>
              </AetherCard>
            </motion.div>
          ) : (
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {activeTab === 'trends' && (
                <div className="space-y-6">
                  <FloatingCard>
                    <TrendExplorer productId={selectedProductId} />
                  </FloatingCard>
                </div>
              )}
              {activeTab === 'forecast' && (
                <div className="space-y-6">
                  <FloatingCard>
                    <ForecastDisplay productId={selectedProductId} />
                  </FloatingCard>
                </div>
              )}
              {activeTab === 'sentiment' && (
                <div className="space-y-6">
                  <FloatingCard>
                    <SentimentPanel productId={selectedProductId} />
                  </FloatingCard>
                </div>
              )}
              {activeTab === 'retailers' && (
                <div className="space-y-6">
                  <FloatingCard>
                    <RetailerComparison productId={selectedProductId} />
                  </FloatingCard>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Floating Action */}
        <motion.div
          className="fixed bottom-8 right-8"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 1, type: 'spring' }}
        >
          <AetherButton
            variant="primary"
            size="lg"
            onClick={() => loadOverview()}
          >
            <Zap className="h-5 w-5" />
            Refresh
          </AetherButton>
        </motion.div>
      </div>
    </div>
  );
};
