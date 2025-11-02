/**
 * Floating Card with 3D Tilt Effect
 * Interactive card that floats and tilts on hover
 */

import React, { useRef, useState } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

interface FloatingCardProps {
  children: React.ReactNode;
  className?: string;
  intensity?: number;
  glowColor?: string;
}

export const FloatingCard: React.FC<FloatingCardProps> = ({
  children,
  className = '',
  intensity = 20,
  glowColor = 'rgba(59, 130, 246, 0.3)'
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);

  // Mouse position
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // Spring animation for smooth movement
  const springConfig = { stiffness: 300, damping: 30 };
  const rotateX = useSpring(useTransform(mouseY, [-0.5, 0.5], [intensity, -intensity]), springConfig);
  const rotateY = useSpring(useTransform(mouseX, [-0.5, 0.5], [-intensity, intensity]), springConfig);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;

    const rect = cardRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    mouseX.set((e.clientX - centerX) / rect.width);
    mouseY.set((e.clientY - centerY) / rect.height);
  };

  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
    setIsHovered(false);
  };

  return (
    <motion.div
      ref={cardRef}
      className={`relative ${className}`}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX,
        rotateY,
        transformStyle: 'preserve-3d',
        perspective: 1000
      }}
      whileHover={{ 
        scale: 1.02,
        transition: { duration: 0.3 }
      }}
      animate={{
        y: isHovered ? -10 : 0
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
    >
      {/* Glow Effect */}
      <motion.div
        className="absolute -inset-1 rounded-2xl opacity-0 transition-opacity duration-300"
        style={{
          background: `radial-gradient(circle at center, ${glowColor}, transparent 70%)`,
          filter: 'blur(20px)',
          opacity: isHovered ? 1 : 0
        }}
        animate={{
          scale: isHovered ? [1, 1.1, 1] : 1
        }}
        transition={{
          duration: 2,
          repeat: isHovered ? Infinity : 0,
          ease: 'easeInOut'
        }}
      />

      {/* Card Content */}
      <div
        className="relative z-10 rounded-2xl bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl 
                   shadow-xl border border-white/20 overflow-hidden"
        style={{ transform: 'translateZ(50px)' }}
      >
        {children}

        {/* Shine Effect on Hover */}
        {isHovered && (
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none"
            initial={{ x: '-100%', skewX: -20 }}
            animate={{ x: '200%' }}
            transition={{
              duration: 0.8,
              ease: 'easeInOut'
            }}
          />
        )}
      </div>

      {/* Floating particles */}
      {isHovered && (
        <>
          {[...Array(5)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 rounded-full bg-blue-400/50"
              style={{
                left: `${20 + i * 15}%`,
                bottom: 0
              }}
              initial={{ y: 0, opacity: 1 }}
              animate={{ 
                y: -100, 
                opacity: 0,
                x: Math.random() * 40 - 20
              }}
              transition={{
                duration: 1 + Math.random() * 0.5,
                repeat: Infinity,
                delay: i * 0.1
              }}
            />
          ))}
        </>
      )}
    </motion.div>
  );
};
