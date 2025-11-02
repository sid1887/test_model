import { motion } from 'framer-motion';
import { ReactNode } from 'react';

export function HaloText({ children }: { children: ReactNode }) {
  return (
    <div className="relative inline-block">
      <motion.div
        className="absolute -inset-6 rounded-full bg-gradient-to-r from-fuchsia-500/20 via-purple-500/10 to-sky-500/20 blur-2xl"
        animate={{ opacity: [0.2, 0.4, 0.2], scale: [0.98, 1.02, 0.98] }}
        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
      />
      <span className="relative bg-clip-text text-transparent bg-gradient-to-r from-fuchsia-500 via-purple-500 to-sky-500">
        {children}
      </span>
    </div>
  );
}

export default HaloText;
