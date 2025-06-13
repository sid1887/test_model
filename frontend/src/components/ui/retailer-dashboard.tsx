import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Store, CheckCircle, XCircle, Clock, Star, Users, TrendingUp, Info } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

interface RetailerConfig {
  key: string;
  name: string;
  domain: string;
  category: string;
  priority: string;
  status: 'active' | 'inactive' | 'maintenance';
  logo?: string;
  description: string;
  features: string[];
  stats: {
    listings: number;
    avgPrice: number;
    responseTime: number;
    successRate: number;
  };
}

interface RetailerDashboardProps {
  onRetailerToggle?: (retailerKey: string, status: string) => void;
  onRetailerConfig?: (retailerKey: string) => void;
  className?: string;
}

// Mock retailer data - in real app, this would come from API
const MOCK_RETAILERS: RetailerConfig[] = [
  // Tier 1 - High Priority
  {
    key: 'amazon',
    name: 'Amazon',
    domain: 'amazon.com',
    category: 'GENERAL',
    priority: 'HIGH',
    status: 'active',
    description: 'World\'s largest online marketplace with vast product selection',
    features: ['Prime shipping', 'Reviews', 'Wide selection', 'AI recommendations'],
    stats: { listings: 2500000, avgPrice: 45.99, responseTime: 1.2, successRate: 98.5 }
  },
  {
    key: 'walmart',
    name: 'Walmart',
    domain: 'walmart.com',
    category: 'GENERAL',
    priority: 'HIGH',
    status: 'active',
    description: 'America\'s largest retailer with competitive everyday low prices',
    features: ['Everyday low prices', 'Grocery delivery', 'Store pickup', 'Wide network'],
    stats: { listings: 1800000, avgPrice: 42.50, responseTime: 1.5, successRate: 96.2 }
  },
  {
    key: 'target',
    name: 'Target',
    domain: 'target.com',
    category: 'GENERAL',
    priority: 'HIGH',
    status: 'active',
    description: 'Premium discount retailer known for trendy, quality products',
    features: ['Designer partnerships', 'REDcard benefits', 'Same-day delivery', 'Quality brands'],
    stats: { listings: 950000, avgPrice: 38.75, responseTime: 1.8, successRate: 94.8 }
  },
  {
    key: 'bestbuy',
    name: 'Best Buy',
    domain: 'bestbuy.com',
    category: 'ELECTRONICS',
    priority: 'HIGH',
    status: 'active',
    description: 'Leading electronics retailer with expert advice and services',
    features: ['Geek Squad support', 'Price matching', 'Expert reviews', 'Tech services'],
    stats: { listings: 450000, avgPrice: 299.99, responseTime: 2.1, successRate: 93.5 }
  },
  {
    key: 'ebay',
    name: 'eBay',
    domain: 'ebay.com',
    category: 'GENERAL',
    priority: 'HIGH',
    status: 'active',
    description: 'Global marketplace for new and used items with auction features',
    features: ['Auction format', 'Global reach', 'Collectibles', 'Buyer protection'],
    stats: { listings: 1200000, avgPrice: 67.25, responseTime: 2.3, successRate: 91.7 }
  },

  // Tier 2 - Medium Priority
  {
    key: 'costco',
    name: 'Costco',
    domain: 'costco.com',
    category: 'WHOLESALE',
    priority: 'MEDIUM',
    status: 'active',
    description: 'Membership-based warehouse club with bulk purchasing options',
    features: ['Bulk pricing', 'Kirkland brand', 'Member benefits', 'Quality guarantee'],
    stats: { listings: 125000, avgPrice: 89.99, responseTime: 2.8, successRate: 89.2 }
  },
  {
    key: 'homedepot',
    name: 'Home Depot',
    domain: 'homedepot.com',
    category: 'HOME_IMPROVEMENT',
    priority: 'MEDIUM',
    status: 'active',
    description: 'Home improvement superstore with tools and building materials',
    features: ['Pro services', 'Installation', 'Tool rental', 'DIY guides'],
    stats: { listings: 750000, avgPrice: 156.50, responseTime: 2.5, successRate: 92.1 }
  },
  {
    key: 'lowes',
    name: 'Lowe\'s',
    domain: 'lowes.com',
    category: 'HOME_IMPROVEMENT',
    priority: 'MEDIUM',
    status: 'active',
    description: 'Home improvement retailer with focus on customer service',
    features: ['Expert advice', 'Installation services', 'Pro rewards', 'Local delivery'],
    stats: { listings: 680000, avgPrice: 142.75, responseTime: 2.7, successRate: 90.8 }
  },
  {
    key: 'newegg',
    name: 'Newegg',
    domain: 'newegg.com',
    category: 'ELECTRONICS',
    priority: 'MEDIUM',
    status: 'active',
    description: 'Technology-focused retailer popular with PC enthusiasts',
    features: ['PC building', 'Tech reviews', 'Gaming focus', 'DIY computer parts'],
    stats: { listings: 320000, avgPrice: 425.99, responseTime: 3.1, successRate: 88.6 }
  },
  {
    key: 'macys',
    name: 'Macy\'s',
    domain: 'macys.com',
    category: 'FASHION',
    priority: 'MEDIUM',
    status: 'active',
    description: 'Premium department store with fashion and home goods',
    features: ['Designer brands', 'Star rewards', 'Personal shopping', 'Fashion expertise'],
    stats: { listings: 425000, avgPrice: 78.25, responseTime: 2.9, successRate: 87.4 }
  },

  // Tier 3 - Low Priority (Specialty)
  {
    key: 'overstock',
    name: 'Overstock',
    domain: 'overstock.com',
    category: 'SPECIALTY',
    priority: 'LOW',
    status: 'active',
    description: 'Online retailer specializing in home goods and furniture',
    features: ['Home decor', 'Furniture deals', 'Closeout prices', 'Unique finds'],
    stats: { listings: 180000, avgPrice: 195.50, responseTime: 3.5, successRate: 85.2 }
  },
  {
    key: 'wayfair',
    name: 'Wayfair',
    domain: 'wayfair.com',
    category: 'HOME_IMPROVEMENT',
    priority: 'LOW',
    status: 'active',
    description: 'Specialized home goods and furniture online retailer',
    features: ['Home focus', 'Room visualization', 'Professional services', 'Style guides'],
    stats: { listings: 890000, avgPrice: 267.99, responseTime: 3.2, successRate: 86.1 }
  },
  {
    key: 'zappos',
    name: 'Zappos',
    domain: 'zappos.com',
    category: 'FASHION',
    priority: 'LOW',
    status: 'active',
    description: 'Online shoe and clothing retailer known for exceptional service',
    features: ['Free shipping', '365-day returns', 'Exceptional service', 'Shoe focus'],
    stats: { listings: 285000, avgPrice: 89.99, responseTime: 2.4, successRate: 94.2 }
  },
  {
    key: 'bhphoto',
    name: 'B&H Photo',
    domain: 'bhphotovideo.com',
    category: 'ELECTRONICS',
    priority: 'LOW',
    status: 'active',
    description: 'Professional photography and video equipment specialist',
    features: ['Pro equipment', 'Expert advice', 'Rental services', 'Education'],
    stats: { listings: 165000, avgPrice: 899.99, responseTime: 2.8, successRate: 91.5 }
  },
  {
    key: 'nordstrom',
    name: 'Nordstrom',
    domain: 'nordstrom.com',
    category: 'FASHION',
    priority: 'LOW',
    status: 'maintenance',
    description: 'Luxury department store with premium fashion and beauty',
    features: ['Luxury brands', 'Personal stylists', 'Nordstrom Rack', 'Premium service'],
    stats: { listings: 195000, avgPrice: 156.75, responseTime: 4.1, successRate: 82.3 }
  }
];

const CATEGORY_INFO = {
  GENERAL: { name: 'General Merchandise', color: 'bg-blue-500', icon: Store },
  ELECTRONICS: { name: 'Electronics & Tech', color: 'bg-purple-500', icon: TrendingUp },
  FASHION: { name: 'Fashion & Apparel', color: 'bg-pink-500', icon: Star },
  HOME_IMPROVEMENT: { name: 'Home & Garden', color: 'bg-green-500', icon: Users },
  WHOLESALE: { name: 'Wholesale & Bulk', color: 'bg-orange-500', icon: TrendingUp },
  SPECIALTY: { name: 'Specialty Online', color: 'bg-gray-500', icon: Info }
};

const PRIORITY_INFO = {
  HIGH: { name: 'High Priority', color: 'bg-green-500' },
  MEDIUM: { name: 'Medium Priority', color: 'bg-yellow-500' },
  LOW: { name: 'Low Priority', color: 'bg-gray-500' }
};

const RetailerDashboard: React.FC<RetailerDashboardProps> = ({
  onRetailerToggle,
  onRetailerConfig,
  className
}) => {
  const [retailers, setRetailers] = useState<RetailerConfig[]>(MOCK_RETAILERS);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('priority');

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'maintenance':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'inactive':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Info className="w-4 h-4 text-gray-500" />;
    }
  };

  const filteredRetailers = retailers.filter(retailer => 
    selectedCategory === 'all' || retailer.category === selectedCategory
  );
  const sortedRetailers = [...filteredRetailers].sort((a, b) => {
    switch (sortBy) {
      case 'priority': {
        const priorityOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 };
        return priorityOrder[a.priority as keyof typeof priorityOrder] - priorityOrder[b.priority as keyof typeof priorityOrder];
      }
      case 'name':
        return a.name.localeCompare(b.name);
      case 'successRate':
        return b.stats.successRate - a.stats.successRate;
      case 'listings':
        return b.stats.listings - a.stats.listings;
      default:
        return 0;
    }
  });

  const activeRetailers = retailers.filter(r => r.status === 'active').length;
  const totalListings = retailers.reduce((sum, r) => sum + r.stats.listings, 0);
  const avgSuccessRate = retailers.reduce((sum, r) => sum + r.stats.successRate, 0) / retailers.length;

  return (
    <div className={cn("w-full space-y-6", className)}>
      {/* Dashboard Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Retailer Management
          </h2>
          <p className="text-muted-foreground mt-1">
            Monitor and configure 15+ integrated retail partners
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 lg:gap-6">
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{activeRetailers}</div>
            <div className="text-xs text-muted-foreground">Active Retailers</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">{(totalListings / 1000000).toFixed(1)}M</div>
            <div className="text-xs text-muted-foreground">Total Listings</div>
          </Card>
          <Card className="p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{avgSuccessRate.toFixed(1)}%</div>
            <div className="text-xs text-muted-foreground">Avg Success Rate</div>
          </Card>
        </div>
      </div>

      {/* Filters and Controls */}
      <Tabs defaultValue="all" className="w-full">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <TabsList className="grid w-full sm:w-auto grid-cols-3 lg:grid-cols-7">
            <TabsTrigger value="all" onClick={() => setSelectedCategory('all')}>All</TabsTrigger>
            {Object.entries(CATEGORY_INFO).map(([key, info]) => (
              <TabsTrigger 
                key={key} 
                value={key.toLowerCase()}
                onClick={() => setSelectedCategory(key)}
                className="hidden lg:flex"
              >
                {info.name.split(' ')[0]}
              </TabsTrigger>
            ))}
          </TabsList>

          <div className="flex gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 rounded-md border border-input bg-background text-sm"
            >
              <option value="priority">Sort by Priority</option>
              <option value="name">Sort by Name</option>
              <option value="successRate">Sort by Success Rate</option>
              <option value="listings">Sort by Listings</option>
            </select>
          </div>
        </div>

        {/* Retailer Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedRetailers.map((retailer, index) => {
            const categoryInfo = CATEGORY_INFO[retailer.category as keyof typeof CATEGORY_INFO];
            const priorityInfo = PRIORITY_INFO[retailer.priority as keyof typeof PRIORITY_INFO];
            
            return (
              <motion.div
                key={retailer.key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="p-6 hover:shadow-lg transition-all duration-300 h-full">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", categoryInfo.color)}>
                        <categoryInfo.icon className="w-5 h-5 text-white" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">{retailer.name}</h3>
                        <p className="text-sm text-muted-foreground">{retailer.domain}</p>
                      </div>
                    </div>
                    {getStatusIcon(retailer.status)}
                  </div>

                  {/* Badges */}
                  <div className="flex gap-2 mb-4">
                    <Badge variant="secondary" className="text-xs">
                      {categoryInfo.name}
                    </Badge>
                    <Badge 
                      className={cn("text-xs text-white", priorityInfo.color)}
                    >
                      {priorityInfo.name}
                    </Badge>
                  </div>

                  {/* Description */}
                  <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                    {retailer.description}
                  </p>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="text-center p-2 bg-muted/50 rounded">
                      <div className="text-sm font-semibold">{(retailer.stats.listings / 1000).toFixed(0)}K</div>
                      <div className="text-xs text-muted-foreground">Listings</div>
                    </div>
                    <div className="text-center p-2 bg-muted/50 rounded">
                      <div className="text-sm font-semibold">{retailer.stats.successRate}%</div>
                      <div className="text-xs text-muted-foreground">Success</div>
                    </div>
                  </div>

                  {/* Features */}
                  <div className="mb-4">
                    <div className="text-xs font-medium mb-2">Key Features</div>
                    <div className="flex flex-wrap gap-1">
                      {retailer.features.slice(0, 3).map((feature) => (
                        <Badge key={feature} variant="outline" className="text-xs">
                          {feature}
                        </Badge>
                      ))}
                      {retailer.features.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{retailer.features.length - 3} more
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      variant={retailer.status === 'active' ? 'destructive' : 'default'}
                      size="sm"
                      className="flex-1"
                      onClick={() => onRetailerToggle?.(retailer.key, retailer.status === 'active' ? 'inactive' : 'active')}
                    >
                      {retailer.status === 'active' ? 'Disable' : 'Enable'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onRetailerConfig?.(retailer.key)}
                    >
                      <Info className="w-4 h-4" />
                    </Button>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </Tabs>
    </div>
  );
};

export { RetailerDashboard };
export type { RetailerConfig };
