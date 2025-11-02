/**
 * Aether Lazy Loading Utilities
 * Performance-optimized component lazy loading with suspense boundaries
 */

import React, { Suspense, ComponentType } from 'react';
import { AetherSkeletonCard } from '@/components/angel/AetherSkeleton';

/**
 * Lazy load a component with automatic retry on failure
 */
export const lazyWithRetry = <T extends ComponentType<any>>(
  componentImport: () => Promise<{ default: T }>,
  retries = 3,
  interval = 1000
): React.LazyExoticComponent<T> => {
  return React.lazy(() => {
    return new Promise<{ default: T }>((resolve, reject) => {
      const attemptLoad = (attemptsLeft: number) => {
        componentImport()
          .then(resolve)
          .catch((error) => {
            if (attemptsLeft === 1) {
              reject(error);
              return;
            }
            
            console.warn(
              `Failed to load component. Retrying... (${retries - attemptsLeft + 1}/${retries})`
            );
            
            setTimeout(() => {
              attemptLoad(attemptsLeft - 1);
            }, interval);
          });
      };

      attemptLoad(retries);
    });
  });
};

/**
 * Lazy load with custom fallback
 */
interface LazyLoadOptions {
  fallback?: React.ReactNode;
  onError?: (error: Error) => void;
}

export const LazyLoad: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ children, fallback = <AetherSkeletonCard /> }) => {
  return (
    <Suspense fallback={fallback}>
      {children}
    </Suspense>
  );
};

/**
 * Error boundary for lazy-loaded components
 */
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class LazyLoadErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('LazyLoad Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="p-4 text-center text-muted-foreground">
          <p>Failed to load component</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="mt-2 px-4 py-2 bg-aether-primary text-white rounded-lg"
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * HOC to wrap component with lazy loading and error boundary
 */
export const withLazyLoad = <P extends object>(
  Component: ComponentType<P>,
  options: LazyLoadOptions = {}
) => {
  const LazyComponent = lazyWithRetry(() =>
    Promise.resolve({ default: Component })
  );

  return (props: P) => (
    <LazyLoadErrorBoundary fallback={options.fallback}>
      <LazyLoad fallback={options.fallback}>
        <LazyComponent {...props} />
      </LazyLoad>
    </LazyLoadErrorBoundary>
  );
};

/**
 * Preload a lazy component
 */
export const preloadComponent = (
  componentImport: () => Promise<{ default: ComponentType<any> }>
) => {
  return componentImport();
};

/**
 * Intersection observer for lazy loading on scroll
 */
export const useLazyLoadOnScroll = (
  ref: React.RefObject<HTMLElement>,
  callback: () => void,
  options: IntersectionObserverInit = {}
) => {
  React.useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          callback();
          observer.disconnect();
        }
      },
      {
        threshold: 0.1,
        ...options,
      }
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [ref, callback, options]);
};

export default {
  lazyWithRetry,
  LazyLoad,
  LazyLoadErrorBoundary,
  withLazyLoad,
  preloadComponent,
  useLazyLoadOnScroll,
};
