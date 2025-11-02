import React from 'react';
import { motion } from 'framer-motion';

interface StaggerGridProps {
  children: React.ReactNode;
  className?: string;
  staggerDelay?: number;
  animationType?: 'fade' | 'slide' | 'scale' | 'rotate';
}

const StaggerGrid: React.FC<StaggerGridProps> = ({
  children,
  className = '',
  staggerDelay = 0.05,
  animationType = 'slide',
}) => {
  const animationVariants = {
    fade: {
      hidden: { opacity: 0 },
      visible: { opacity: 1 },
    },
    slide: {
      hidden: { opacity: 0, y: 30 },
      visible: { opacity: 1, y: 0 },
    },
    scale: {
      hidden: { opacity: 0, scale: 0.8 },
      visible: { opacity: 1, scale: 1 },
    },
    rotate: {
      hidden: { opacity: 0, rotateY: -20, scale: 0.9 },
      visible: { opacity: 1, rotateY: 0, scale: 1 },
    },
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: staggerDelay,
        delayChildren: 0.1,
      },
    },
  };

  return (
    <motion.div
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {React.Children.map(children, (child, index) => (
        <motion.div
          key={index}
          variants={animationVariants[animationType]}
          transition={{
            duration: 0.5,
            ease: [0.25, 0.1, 0.25, 1], // Aether cubic-bezier
          }}
        >
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
};

export default StaggerGrid;
