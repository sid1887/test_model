/**
 * Aether Motion Utilities
 * Respects user's motion preferences and provides optimized animation variants
 */

import { useEffect, useState } from 'react';
import { Variants } from 'framer-motion';

/**
 * Hook to detect user's reduced motion preference
 */
export const usePrefersReducedMotion = (): boolean => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
    // Legacy browsers
    else {
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, []);

  return prefersReducedMotion;
};

/**
 * Get animation variants that respect user's motion preferences
 */
export const getMotionVariants = (
  prefersReducedMotion: boolean,
  variants: Variants,
  reducedVariants?: Variants
): Variants => {
  if (prefersReducedMotion && reducedVariants) {
    return reducedVariants;
  }
  if (prefersReducedMotion) {
    // Disable all animations
    return {
      initial: { opacity: 1 },
      animate: { opacity: 1 },
      exit: { opacity: 1 },
    };
  }
  return variants;
};

/**
 * Standard Aether motion variants with reduced motion alternatives
 */
export const aetherMotionVariants = {
  // Fade In/Out
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },
  fadeReduced: {
    initial: { opacity: 1 },
    animate: { opacity: 1 },
    exit: { opacity: 1 },
  },

  // Slide Up
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  },
  slideUpReduced: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },

  // Scale
  scale: {
    initial: { opacity: 0, scale: 0.8 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.8 },
  },
  scaleReduced: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },

  // Rotate Scale
  rotateScale: {
    initial: { opacity: 0, scale: 0.8, rotateY: -20 },
    animate: { opacity: 1, scale: 1, rotateY: 0 },
    exit: { opacity: 0, scale: 0.8, rotateY: 20 },
  },
  rotateScaleReduced: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },
};

/**
 * Get transition config that respects motion preferences
 */
export const getTransition = (prefersReducedMotion: boolean, duration = 0.3) => {
  if (prefersReducedMotion) {
    return { duration: 0 };
  }
  return {
    duration,
    ease: [0.25, 0.1, 0.25, 1], // Aether cubic-bezier
  };
};

/**
 * Performance monitoring utilities
 */
export const measurePerformance = (name: string, callback: () => void) => {
  const start = performance.now();
  callback();
  const end = performance.now();
  const duration = end - start;

  if (duration > 16.67) { // Longer than one frame (60fps)
    console.warn(`Performance: ${name} took ${duration.toFixed(2)}ms (> 16.67ms)`);
  }

  return duration;
};

/**
 * Debounce for performance-critical operations
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Throttle for scroll/resize handlers
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

export default {
  usePrefersReducedMotion,
  getMotionVariants,
  aetherMotionVariants,
  getTransition,
  measurePerformance,
  debounce,
  throttle,
};
