
import { lazy } from 'react';
import { SuspenseWrapper } from '@/components/ui/loading-system';

const Index = lazy(() => import('./Index'));

const LazyIndex = () => (
  <SuspenseWrapper
    loadingType="spinner"
    loadingMessage="Loading homepage..."
  >
    <Index />
  </SuspenseWrapper>
);

export default LazyIndex;
