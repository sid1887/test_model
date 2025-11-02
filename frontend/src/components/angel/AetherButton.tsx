import React, { useState } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AetherButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost' | 'accent' | 'glass';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  loadingText?: string;
  glow?: boolean;
}

/**
 * Aether Button - Enhanced with gradient shifts, glow effects, and smooth state transitions
 */
export function AetherButton({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  loadingText,
  glow = false,
  className,
  disabled,
  ...props
}: AetherButtonProps) {
  const [backgroundPosition, setBackgroundPosition] = useState('0% 50%');

  const baseClasses = "relative overflow-hidden font-semibold rounded-2xl aether-transition inline-flex items-center justify-center gap-2";
  
  const variants = {
    primary: cn(
      "bg-gradient-to-r from-aether-primary via-aether-glow to-aether-primary text-white shadow-aether",
      "hover:shadow-aether-lg",
      glow && "hover:shadow-glow"
    ),
    accent: cn(
      "bg-gradient-to-r from-aether-accent via-aether-primary to-aether-accent text-white shadow-float",
      "hover:shadow-glow-accent"
    ),
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80 shadow-sm",
    ghost: "hover:bg-accent hover:text-accent-foreground",
    glass: "glass-elevated hover:bg-white/20 dark:hover:bg-white/10 text-foreground"
  };

  const sizes = {
    sm: "px-4 py-2 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg"
  };

  const isDisabled = disabled || isLoading;

  return (
    <motion.button
      className={cn(
        baseClasses,
        variants[variant],
        sizes[size],
        isDisabled && "opacity-50 cursor-not-allowed",
        className
      )}
      disabled={isDisabled}
      whileHover={!isDisabled ? { 
        scale: 1.05,
        backgroundSize: '200% 200%',
      } : undefined}
      whileTap={!isDisabled ? { scale: 0.98 } : undefined}
      animate={
        (variant === 'primary' || variant === 'accent') ? {
          backgroundPosition: [backgroundPosition, '100% 50%', '0% 50%']
        } : undefined
      }
      transition={{
        backgroundPosition: {
          duration: 5,
          repeat: Infinity,
          ease: 'linear'
        },
        scale: {
          type: 'spring',
          stiffness: 400,
          damping: 17
        }
      }}
      style={{
        backgroundSize: '200% 200%',
        willChange: 'transform'
      }}
      onHoverStart={() => setBackgroundPosition('100% 50%')}
      onHoverEnd={() => setBackgroundPosition('0% 50%')}
      {...props}
    >
      {/* Loading Spinner */}
      {isLoading && (
        <Loader2 className="absolute right-4 h-4 w-4 animate-spin" />
      )}
      
      {/* Content */}
      <span className={cn("relative z-10", isLoading && "opacity-0")}>
        {children}
      </span>
      
      {/* Loading Text */}
      {isLoading && loadingText && (
        <span className="relative z-10">{loadingText}</span>
      )}

      {/* Hover Overlay */}
      {!isDisabled && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0"
          initial={{ opacity: 0 }}
          whileHover={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        />
      )}
    </motion.button>
  );
}

export default AetherButton;
