
import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Clock, Zap } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface SmartInsightProps {
  priceChange: number;
  valueScore: number;
  reviewCount: number;
  store: string;
  className?: string;
}

const SmartProductInsights: React.FC<SmartInsightProps> = ({
  priceChange,
  valueScore,
  reviewCount,
  store,
  className
}) => {
  const getPriceInsight = () => {
    if (priceChange > 5) return { icon: TrendingUp, text: 'Price Rising', color: 'text-red-500', bg: 'bg-red-500/10' };
    if (priceChange < -3) return { icon: TrendingDown, text: 'Great Deal', color: 'text-green-500', bg: 'bg-green-500/10' };
    return { icon: Clock, text: 'Stable Price', color: 'text-blue-500', bg: 'bg-blue-500/10' };
  };

  const getValueInsight = () => {
    if (valueScore >= 4.5) return { icon: CheckCircle, text: 'Best Value', color: 'text-green-500' };
    if (valueScore >= 3.5) return { icon: Zap, text: 'Good Value', color: 'text-blue-500' };
    return { icon: AlertTriangle, text: 'Consider Alternatives', color: 'text-orange-500' };
  };

  const getTrustLevel = () => {
    if (reviewCount > 2000) return 'High Trust';
    if (reviewCount > 500) return 'Verified';
    return 'New Product';
  };

  const priceInsight = getPriceInsight();
  const valueInsight = getValueInsight();

  return (
    <div className={cn("space-y-2", className)}>
      {/* AI Price Insight */}
      <motion.div 
        className={cn("flex items-center gap-2 px-2 py-1 rounded-lg", priceInsight.bg)}
        whileHover={{ scale: 1.02 }}
      >
        <priceInsight.icon className={cn("w-3 h-3", priceInsight.color)} />
        <span className={cn("text-xs font-medium", priceInsight.color)}>
          {priceInsight.text}
        </span>
        <span className="text-xs text-muted-foreground">
          {Math.abs(priceChange)}%
        </span>
      </motion.div>

      {/* Value Score Insight */}
      <motion.div 
        className="flex items-center gap-2"
        whileHover={{ scale: 1.02 }}
      >
        <valueInsight.icon className={cn("w-3 h-3", valueInsight.color)} />
        <span className={cn("text-xs font-medium", valueInsight.color)}>
          {valueInsight.text}
        </span>
      </motion.div>

      {/* Trust Badge */}
      <Badge variant="secondary" className="text-xs">
        {getTrustLevel()}
      </Badge>
    </div>
  );
};

export { SmartProductInsights };
