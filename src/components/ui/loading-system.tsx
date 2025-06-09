
import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', className }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  return (
    <motion.div
      className={cn('relative', sizes[size], className)}
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    >
      <div className="absolute inset-0 border-2 border-primary/30 rounded-full" />
      <div className="absolute inset-0 border-2 border-transparent border-t-primary rounded-full" />
    </motion.div>
  );
};

interface SkeletonTextProps {
  lines?: number;
  className?: string;
}

const SkeletonText: React.FC<SkeletonTextProps> = ({ lines = 1, className }) => {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }, (_, i) => (
        <motion.div
          key={i}
          className={cn(
            'h-4 bg-gradient-to-r from-muted via-muted/50 to-muted rounded',
            i === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'
          )}
          animate={{
            backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'linear',
          }}
          style={{
            backgroundSize: '200% 100%',
          }}
        />
      ))}
    </div>
  );
};

interface LoadingStateProps {
  type: 'spinner' | 'skeleton' | 'dots';
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const LoadingState: React.FC<LoadingStateProps> = ({ 
  type, 
  message, 
  size = 'md', 
  className 
}) => {
  if (type === 'spinner') {
    return (
      <div className={cn('flex flex-col items-center justify-center p-8', className)}>
        <LoadingSpinner size={size} />
        {message && (
          <p className="mt-4 text-sm text-muted-foreground animate-pulse">
            {message}
          </p>
        )}
      </div>
    );
  }

  if (type === 'dots') {
    return (
      <div className={cn('flex items-center justify-center p-8', className)}>
        <div className="flex space-x-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 bg-primary rounded-full"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [1, 0.5, 1],
              }}
              transition={{
                duration: 0.8,
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn('p-6', className)}>
      <SkeletonText lines={3} />
    </div>
  );
};

interface SuspenseWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  loadingType?: 'spinner' | 'skeleton' | 'dots';
  loadingMessage?: string;
}

const SuspenseWrapper: React.FC<SuspenseWrapperProps> = ({
  children,
  fallback,
  loadingType = 'spinner',
  loadingMessage = 'Loading...'
}) => {
  const defaultFallback = (
    <LoadingState
      type={loadingType}
      message={loadingMessage}
      className="min-h-[200px]"
    />
  );

  return (
    <React.Suspense fallback={fallback || defaultFallback}>
      {children}
    </React.Suspense>
  );
};

export { LoadingSpinner, SkeletonText, LoadingState, SuspenseWrapper };
