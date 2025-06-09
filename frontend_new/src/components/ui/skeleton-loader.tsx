
import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'default' | 'card' | 'text' | 'avatar';
}

const Skeleton: React.FC<SkeletonProps> = ({ className, variant = 'default' }) => {
  const variants = {
    default: "h-4 w-full",
    card: "h-48 w-full rounded-xl",
    text: "h-4 w-3/4",
    avatar: "h-12 w-12 rounded-full"
  };

  return (
    <motion.div
      className={cn(
        "relative overflow-hidden bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-800 dark:via-gray-700 dark:to-gray-800 rounded-lg",
        variants[variant],
        className
      )}
      animate={{
        backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
      }}
      transition={{
        duration: 1.5,
        repeat: Infinity,
        ease: "linear",
      }}
      style={{
        backgroundSize: "200% 100%",
      }}
    />
  );
};

const ProductCardSkeleton: React.FC = () => {
  return (
    <div className="space-y-4 p-6 bg-white/90 dark:bg-black/80 rounded-2xl border border-white/20 dark:border-white/10">
      <Skeleton variant="card" />
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-4 w-12" />
        </div>
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-8 w-20" />
      </div>
    </div>
  );
};

export { Skeleton, ProductCardSkeleton };
