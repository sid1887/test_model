import { ReactNode } from 'react';

export function GlassPanel({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`backdrop-blur-xl bg-white/60 dark:bg-white/5 border border-white/20 dark:border-white/10 shadow-2xl rounded-2xl ${className}`}>
      {children}
    </div>
  );
}

export default GlassPanel;
