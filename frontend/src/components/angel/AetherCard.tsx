import React, { useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { cn } from '@/lib/utils';

interface AetherCardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'elevated' | 'subtle' | 'glass' | 'solid';
  hover?: boolean;
  tilt?: boolean;
  glow?: boolean;
  onClick?: () => void;
}

/**
 * Aether Card - Glass morphism card with 3D tilt and glow effects
 */
export function AetherCard({
  children,
  className,
  variant = 'elevated',
  hover = true,
  tilt = false,
  glow = false,
  onClick
}: AetherCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const rotateX = useSpring(useTransform(mouseY, [-0.5, 0.5], [5, -5]), {
    stiffness: 300,
    damping: 30
  });
  
  const rotateY = useSpring(useTransform(mouseX, [-0.5, 0.5], [-5, 5]), {
    stiffness: 300,
    damping: 30
  });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!tilt || !cardRef.current) return;

    const rect = cardRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;

    mouseX.set(x);
    mouseY.set(y);
  };

  const handleMouseLeave = () => {
    if (!tilt) return;
    mouseX.set(0);
    mouseY.set(0);
  };

  const variants = {
    elevated: 'glass-elevated',
    subtle: 'glass-subtle',
    glass: 'backdrop-blur-xl bg-white/10 dark:bg-white/5 border border-white/20 dark:border-white/10',
    solid: 'bg-card border-border shadow-lg'
  };

  const glowClasses = glow ? 'hover:shadow-glow' : '';

  return (
    <motion.div
      ref={cardRef}
      className={cn(
        'rounded-2xl p-6 aether-transition cursor-pointer',
        variants[variant],
        glowClasses,
        className
      )}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      whileHover={hover ? {
        y: -8,
        scale: 1.02,
      } : undefined}
      whileTap={hover ? { scale: 0.98 } : undefined}
      style={tilt ? {
        rotateX,
        rotateY,
        transformStyle: 'preserve-3d',
      } : undefined}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 20
      }}
    >
      {/* Conic Border Glow (on hover) */}
      {glow && (
        <motion.div
          className="absolute inset-0 rounded-2xl opacity-0 pointer-events-none"
          style={{
            background: 'conic-gradient(from 0deg, hsl(270 80% 45%), hsl(15 90% 60%), hsl(270 80% 45%))',
            padding: '2px',
            WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
            WebkitMaskComposite: 'xor',
            maskComposite: 'exclude',
          }}
          whileHover={{ opacity: 0.6 }}
          animate={{ rotate: 360 }}
          transition={{
            rotate: {
              duration: 3,
              repeat: Infinity,
              ease: 'linear'
            },
            opacity: {
              duration: 0.3
            }
          }}
        />
      )}

      {/* Content */}
      <div className="relative z-10" style={tilt ? { transform: 'translateZ(20px)' } : undefined}>
        {children}
      </div>
    </motion.div>
  );
}

export default AetherCard;
