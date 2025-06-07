'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'glass' | 'gradient';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  ripple?: boolean;
  glow?: boolean;
}

const buttonVariants = {
  default: 'bg-primary-500 text-white hover:bg-primary-600 focus:ring-primary-500',
  secondary: 'bg-secondary-100 text-secondary-900 hover:bg-secondary-200 dark:bg-secondary-800 dark:text-secondary-100 dark:hover:bg-secondary-700',
  outline: 'border-2 border-primary-500 text-primary-500 hover:bg-primary-500 hover:text-white',
  ghost: 'text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-950',
  glass: 'glass text-gray-900 dark:text-white hover:shadow-glass-dark',
  gradient: 'bg-gradient-to-r from-primary-500 to-accent-500 text-white hover:from-primary-600 hover:to-accent-600',
};

const sizeVariants = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
  xl: 'px-8 py-4 text-xl',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    className,
    variant = 'default',
    size = 'md',
    loading = false,
    icon,
    iconPosition = 'left',
    ripple = true,
    glow = false,
    children,
    disabled,
    onClick,
    ...props
  }, ref) => {
    const [rippleArray, setRippleArray] = React.useState<Array<{
      x: number;
      y: number;
      id: number;
    }>>([]);

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (ripple && !disabled && !loading) {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const id = Date.now();
        
        setRippleArray(prev => [...prev, { x, y, id }]);
        
        setTimeout(() => {
          setRippleArray(prev => prev.filter(ripple => ripple.id !== id));
        }, 600);
      }
      
      if (onClick && !disabled && !loading) {
        onClick(e);
      }
    };

    return (
      <motion.button
        ref={ref}
        className={cn(
          'relative inline-flex items-center justify-center rounded-xl font-medium transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-900 overflow-hidden',
          buttonVariants[variant],
          sizeVariants[size],
          {
            'opacity-50 cursor-not-allowed': disabled || loading,
            'hover:scale-105 active:scale-95': !disabled && !loading,
            'hover:shadow-glow-primary': glow && variant === 'default',
            'hover:shadow-glow-secondary': glow && variant === 'secondary',
            'hover:shadow-glow-accent': glow && variant === 'gradient',
          },
          className
        )}
        disabled={disabled || loading}
        onClick={handleClick}
        whileHover={!disabled && !loading ? { scale: 1.05 } : {}}
        whileTap={!disabled && !loading ? { scale: 0.95 } : {}}
        transition={{ type: 'spring', stiffness: 400, damping: 17 }}
        {...props}
      >
        {/* Ripple Effect */}
        {rippleArray.map(ripple => (
          <motion.span
            key={ripple.id}
            className="absolute rounded-full bg-white opacity-20 pointer-events-none"
            style={{
              left: ripple.x - 10,
              top: ripple.y - 10,
              width: 20,
              height: 20,
            }}
            initial={{ scale: 0, opacity: 0.5 }}
            animate={{ scale: 4, opacity: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
        ))}

        {/* Content */}
        {loading ? (
          <motion.div
            className="flex items-center space-x-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
          >
            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            <span>Loading...</span>
          </motion.div>
        ) : (
          <div className="flex items-center space-x-2">
            {icon && iconPosition === 'left' && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
              >
                {icon}
              </motion.span>
            )}
            
            {children && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.2, delay: 0.1 }}
              >
                {children}
              </motion.span>
            )}
            
            {icon && iconPosition === 'right' && (
              <motion.span
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
              >
                {icon}
              </motion.span>
            )}
          </div>
        )}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
