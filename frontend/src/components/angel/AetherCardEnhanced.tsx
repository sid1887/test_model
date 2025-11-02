import * as React from "react"
import { motion, HTMLMotionProps } from "framer-motion"
import { cn } from "@/lib/utils"

type CardVariant = 'default' | 'glass' | 'elevated' | 'glow';

interface AetherCardEnhancedProps extends HTMLMotionProps<"div"> {
  variant?: CardVariant;
  enableHover?: boolean;
}

const cardVariants: Record<CardVariant, string> = {
  default: "rounded-lg border bg-card text-card-foreground shadow-sm",
  glass: "glass-elevated rounded-2xl border border-white/20 dark:border-white/10",
  elevated: "glass-elevated rounded-2xl border border-white/20 dark:border-white/10 shadow-aether",
  glow: "glass-elevated rounded-2xl border border-aether-glow/30 shadow-glow",
};

const AetherCardEnhanced = React.forwardRef<
  HTMLDivElement,
  AetherCardEnhancedProps
>(({ className, variant = 'default', enableHover = true, children, ...props }, ref) => {
  const hoverAnimation = enableHover ? {
    whileHover: { 
      scale: 1.02,
      boxShadow: variant === 'glow' 
        ? '0 20px 70px -10px hsl(var(--aether-glow) / 0.4)'
        : '0 20px 50px -10px rgba(0, 0, 0, 0.3)',
    },
    transition: {
      duration: 0.3,
      ease: [0.25, 0.1, 0.25, 1],
    },
  } : {};

  return (
    <motion.div
      ref={ref}
      className={cn(cardVariants[variant], className)}
      {...hoverAnimation}
      {...props}
    >
      {children}
    </motion.div>
  );
});
AetherCardEnhanced.displayName = "AetherCardEnhanced"

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight bg-gradient-to-r from-aether-primary to-aether-glow bg-clip-text text-transparent",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { 
  AetherCardEnhanced as Card, 
  CardHeader, 
  CardFooter, 
  CardTitle, 
  CardDescription, 
  CardContent 
}
