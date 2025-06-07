'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'neumorphism' | 'gradient';
  hover?: 'lift' | 'glow' | 'scale' | 'none';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl';
}

const cardVariants = {
  default: 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800',
  glass: 'glass backdrop-blur-xl',
  neumorphism: 'neumorphism-light dark:neumorphism-dark',
  gradient: 'bg-gradient-to-br from-white to-gray-50 dark:from-gray-900 dark:to-gray-800',
};

const hoverVariants = {
  lift: 'hover:-translate-y-2 hover:shadow-2xl',
  glow: 'hover:shadow-glow-primary',
  scale: 'hover:scale-105',
  none: '',
};

const paddingVariants = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8',
};

const roundedVariants = {
  sm: 'rounded-lg',
  md: 'rounded-xl',
  lg: 'rounded-2xl',
  xl: 'rounded-3xl',
  '2xl': 'rounded-4xl',
  '3xl': 'rounded-5xl',
};

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({
    className,
    variant = 'default',
    hover = 'lift',
    padding = 'lg',
    rounded = 'lg',
    children,
    ...props
  }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={cn(
          'transition-all duration-300 ease-out',
          cardVariants[variant],
          hoverVariants[hover],
          paddingVariants[padding],
          roundedVariants[rounded],
          className
        )}
        whileHover={
          hover === 'scale' ? { scale: 1.05 } :
          hover === 'lift' ? { y: -8, scale: 1.02 } :
          {}
        }
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col space-y-1.5 pb-4', className)}
      {...props}
    />
  )
);

CardHeader.displayName = 'CardHeader';

interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {}

export const CardTitle = React.forwardRef<HTMLParagraphElement, CardTitleProps>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        'text-2xl font-semibold leading-none tracking-tight text-gray-900 dark:text-white',
        className
      )}
      {...props}
    />
  )
);

CardTitle.displayName = 'CardTitle';

interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {}

export const CardDescription = React.forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-gray-600 dark:text-gray-300', className)}
      {...props}
    />
  )
);

CardDescription.displayName = 'CardDescription';

interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('', className)} {...props} />
  )
);

CardContent.displayName = 'CardContent';

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center pt-4', className)}
      {...props}
    />
  )
);

CardFooter.displayName = 'CardFooter';
