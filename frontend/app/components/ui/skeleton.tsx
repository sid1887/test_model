'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className,
  variant = 'rectangular',
  width,
  height,
  animation = 'wave',
  ...props
}) => {
  const baseClasses = 'bg-gray-200 dark:bg-gray-700';
  
  const variantClasses = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-shimmer bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 bg-[length:200%_100%]',
    none: '',
  };

  const style: React.CSSProperties = {
    width: width || (variant === 'text' ? '100%' : undefined),
    height: height || (variant === 'text' ? undefined : '1rem'),
  };

  return (
    <div
      className={cn(
        baseClasses,
        variantClasses[variant],
        animationClasses[animation],
        className
      )}
      style={style}
      {...props}
    />
  );
};

interface SkeletonGroupProps {
  lines?: number;
  showAvatar?: boolean;
  showButton?: boolean;
  className?: string;
}

export const SkeletonGroup: React.FC<SkeletonGroupProps> = ({
  lines = 3,
  showAvatar = false,
  showButton = false,
  className,
}) => {
  return (
    <div className={cn('space-y-3', className)}>
      {showAvatar && (
        <div className="flex items-center space-x-3">
          <Skeleton variant="circular" width={40} height={40} />
          <div className="space-y-2 flex-1">
            <Skeleton width="60%" height={16} />
            <Skeleton width="40%" height={14} />
          </div>
        </div>
      )}
      
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, index) => (
          <Skeleton
            key={index}
            width={index === lines - 1 ? '70%' : '100%'}
            height={16}
          />
        ))}
      </div>
      
      {showButton && (
        <div className="flex space-x-2 pt-2">
          <Skeleton width={80} height={36} />
          <Skeleton width={100} height={36} />
        </div>
      )}
    </div>
  );
};

interface ProductCardSkeletonProps {
  className?: string;
}

export const ProductCardSkeleton: React.FC<ProductCardSkeletonProps> = ({
  className,
}) => {
  return (
    <motion.div
      className={cn(
        'p-4 border border-gray-200 dark:border-gray-700 rounded-xl space-y-3',
        className
      )}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Image */}
      <Skeleton height={200} className="rounded-lg" />
      
      {/* Title */}
      <div className="space-y-2">
        <Skeleton height={20} width="80%" />
        <Skeleton height={16} width="60%" />
      </div>
      
      {/* Price */}
      <div className="flex items-center justify-between">
        <Skeleton height={24} width={80} />
        <Skeleton height={20} width={60} />
      </div>
      
      {/* Button */}
      <Skeleton height={40} className="rounded-lg" />
    </motion.div>
  );
};

interface SearchResultsSkeletonProps {
  count?: number;
  className?: string;
}

export const SearchResultsSkeleton: React.FC<SearchResultsSkeletonProps> = ({
  count = 6,
  className,
}) => {
  return (
    <div className={cn('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6', className)}>
      {Array.from({ length: count }).map((_, index) => (
        <ProductCardSkeleton
          key={index}
          className="animate-pulse"
          style={{ animationDelay: `${index * 0.1}s` }}
        />
      ))}
    </div>
  );
};
