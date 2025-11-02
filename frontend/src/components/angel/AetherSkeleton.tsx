import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface AetherSkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'shimmer' | 'pulse' | 'wave';
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

const AetherSkeleton = React.forwardRef<HTMLDivElement, AetherSkeletonProps>(
  ({ className, variant = 'shimmer', rounded = 'md', ...props }, ref) => {
    const roundedClasses = {
      none: '',
      sm: 'rounded-sm',
      md: 'rounded-md',
      lg: 'rounded-lg',
      xl: 'rounded-xl',
      full: 'rounded-full',
    };

    if (variant === 'shimmer') {
      return (
        <div
          ref={ref}
          className={cn(
            "relative overflow-hidden bg-gradient-to-r from-muted/50 via-muted to-muted/50",
            roundedClasses[rounded],
            className
          )}
          {...props}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
            animate={{
              x: ['-100%', '100%'],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        </div>
      );
    }

    if (variant === 'wave') {
      return (
        <div
          ref={ref}
          className={cn(
            "relative overflow-hidden bg-gradient-to-r from-aether-primary/10 via-aether-glow/10 to-aether-primary/10",
            roundedClasses[rounded],
            className
          )}
          {...props}
        >
          <motion.div
            className="absolute inset-0"
            style={{
              background: 'linear-gradient(90deg, transparent, hsl(var(--aether-glow) / 0.3), transparent)',
            }}
            animate={{
              x: ['-100%', '100%'],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        </div>
      );
    }

    if (variant === 'pulse') {
      return (
        <div
          ref={ref}
          className={cn(
            "bg-muted animate-pulse",
            roundedClasses[rounded],
            className
          )}
          {...props}
        />
      );
    }

    // Default
    return (
      <div
        ref={ref}
        className={cn(
          "animate-pulse bg-muted",
          roundedClasses[rounded],
          className
        )}
        {...props}
      />
    );
  }
);
AetherSkeleton.displayName = "AetherSkeleton"

// Preset skeleton components
export const AetherSkeletonText = ({ lines = 3, className }: { lines?: number; className?: string }) => (
  <div className={cn("space-y-2", className)}>
    {Array.from({ length: lines }).map((_, i) => (
      <AetherSkeleton
        key={i}
        variant="shimmer"
        className={cn(
          "h-4",
          i === lines - 1 ? "w-3/4" : "w-full"
        )}
      />
    ))}
  </div>
);

export const AetherSkeletonCard = ({ className }: { className?: string }) => (
  <div className={cn("space-y-4 p-4 glass-elevated rounded-2xl", className)}>
    <AetherSkeleton variant="wave" className="h-48 w-full" rounded="xl" />
    <div className="space-y-2">
      <AetherSkeleton variant="shimmer" className="h-4 w-3/4" />
      <AetherSkeleton variant="shimmer" className="h-4 w-1/2" />
    </div>
    <div className="flex gap-2">
      <AetherSkeleton variant="shimmer" className="h-10 w-24" rounded="lg" />
      <AetherSkeleton variant="shimmer" className="h-10 w-24" rounded="lg" />
    </div>
  </div>
);

export const AetherSkeletonAvatar = ({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) => {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  };

  return (
    <AetherSkeleton
      variant="wave"
      rounded="full"
      className={sizeClasses[size]}
    />
  );
};

export default AetherSkeleton;
