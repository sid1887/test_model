import { motion, useMotionValue, useTransform } from 'framer-motion';
import { ReactNode } from 'react';

export function ParallaxCard({ children }: { children: ReactNode }) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const rotateX = useTransform(y, [-50, 50], [8, -8]);
  const rotateY = useTransform(x, [-50, 50], [-8, 8]);

  return (
    <motion.div
      style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
      onMouseMove={(e) => {
        const rect = (e.target as HTMLElement).getBoundingClientRect();
        const px = e.clientX - rect.left - rect.width / 2;
        const py = e.clientY - rect.top - rect.height / 2;
        x.set(px / 6);
        y.set(py / 6);
      }}
      onMouseLeave={() => { x.set(0); y.set(0); }}
      className="[perspective:1000px] will-change-transform"
    >
      {children}
    </motion.div>
  );
}

export default ParallaxCard;
