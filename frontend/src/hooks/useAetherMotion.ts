import { useInView } from 'framer-motion';
import { useRef } from 'react';

/**
 * Aether Motion Hook - Unified motion state for components
 * Combines scroll reveal, hover states, and animation triggers
 */
export interface AetherMotionConfig {
  /** Threshold for triggering in-view animation (0-1) */
  threshold?: number;
  /** Root margin for intersection observer */
  rootMargin?: string;
  /** Trigger once or repeatedly */
  once?: boolean;
}

export function useAetherMotion(config: AetherMotionConfig = {}) {
  const {
    threshold = 0.1,
    once = true,
  } = config;

  const ref = useRef<HTMLElement>(null);
  const isInView = useInView(ref, {
    once,
    amount: threshold,
  });

  return {
    ref,
    isInView,
    // Pre-configured animation variants
    variants: {
      fadeSlide: {
        hidden: { opacity: 0, y: 50 },
        visible: { 
          opacity: 1, 
          y: 0,
          transition: { 
            duration: 0.6, 
            ease: [0.4, 0, 0.2, 1]
          }
        }
      },
      fadeScale: {
        hidden: { opacity: 0, scale: 0.95 },
        visible: { 
          opacity: 1, 
          scale: 1,
          transition: { 
            duration: 0.5, 
            ease: [0.4, 0, 0.2, 1]
          }
        }
      },
      rotateScale: {
        hidden: { opacity: 0, scale: 0.9, rotate: -5 },
        visible: { 
          opacity: 1, 
          scale: 1, 
          rotate: 0,
          transition: { 
            duration: 0.7, 
            ease: [0.34, 1.56, 0.64, 1]
          }
        }
      },
      stagger: {
        visible: {
          transition: {
            staggerChildren: 0.1
          }
        }
      }
    }
  };
}

/**
 * Parallax scroll hook - Creates depth with scroll
 */
export function useParallaxScroll(multiplier: number = 0.5) {
  // This would typically use useScroll and useTransform from framer-motion
  // For now, returning a simplified version
  return {
    multiplier,
    // This would be connected to actual scroll values
    transform: `translateY(0px)`
  };
}
