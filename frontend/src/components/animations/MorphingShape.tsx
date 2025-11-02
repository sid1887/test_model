/**
 * Morphing Shape Animation
 * Smooth morphing between different shapes
 */

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface MorphingShapeProps {
  size?: number;
  colors?: string[];
  speed?: number;
  blur?: number;
  className?: string;
}

export const MorphingShape: React.FC<MorphingShapeProps> = ({
  size = 200,
  colors = ['#3b82f6', '#8b5cf6', '#ec4899'],
  speed = 8,
  blur = 40,
  className = ''
}) => {
  const [currentShape, setCurrentShape] = useState(0);

  // Different blob shapes (SVG paths)
  const shapes = [
    'M30.5,-41.3C38.5,-33.7,43.2,-23.8,46.6,-13.2C50,-2.6,52.1,8.7,49.3,19C46.5,29.3,38.8,38.6,29.1,43.8C19.4,49,7.7,50.1,-3.5,49.9C-14.7,49.7,-25.4,48.2,-34.3,42.6C-43.2,37,-50.3,27.3,-53.1,16.5C-55.9,5.7,-54.4,-6.2,-49.5,-16.3C-44.6,-26.4,-36.3,-34.7,-27,-41.7C-17.7,-48.7,-8.8,-54.4,1.1,-55.9C11,-57.4,22.5,-54.8,30.5,-41.3Z',
    'M37.1,-51.7C47.3,-42.9,54.5,-30.9,57.5,-18C60.5,-5.1,59.3,8.7,54.1,20.7C48.9,32.7,39.7,43,28.5,49.1C17.3,55.2,4.1,57.1,-9.3,56.3C-22.7,55.5,-36.3,52,-45.8,43.9C-55.3,35.8,-60.7,23.1,-61.4,10.2C-62.1,-2.7,-58.1,-15.8,-51.1,-26.7C-44.1,-37.6,-34.1,-46.3,-23,-55C-11.9,-63.7,0.3,-72.4,12.6,-69.8C24.9,-67.2,37.3,-53.3,37.1,-51.7Z',
    'M42.3,-58.1C53.3,-50.6,59.7,-36.7,62.5,-22.5C65.3,-8.3,64.5,6.2,59.8,19C55.1,31.8,46.5,43,35.7,50.4C24.9,57.8,12.5,61.4,-1.1,62.9C-14.7,64.4,-29.4,63.8,-40.4,56.9C-51.4,50,-58.7,36.8,-61.9,22.9C-65.1,9,-64.2,-5.6,-58.8,-17.7C-53.4,-29.8,-43.5,-39.4,-32.5,-46.9C-21.5,-54.4,-9.3,-59.8,3.9,-65.2C17.1,-70.6,34.2,-76,42.3,-58.1Z'
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentShape(prev => (prev + 1) % shapes.length);
    }, speed * 1000);

    return () => clearInterval(interval);
  }, [speed, shapes.length]);

  return (
    <div className={`relative ${className}`} style={{ width: size, height: size }}>
      <svg
        viewBox="0 0 200 200"
        xmlns="http://www.w3.org/2000/svg"
        className="absolute inset-0"
        style={{
          filter: `blur(${blur}px)`
        }}
      >
        <defs>
          <linearGradient id="morphGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            {colors.map((color, index) => (
              <stop
                key={index}
                offset={`${(index / (colors.length - 1)) * 100}%`}
                stopColor={color}
              />
            ))}
          </linearGradient>
        </defs>
        <motion.path
          d={shapes[currentShape]}
          fill="url(#morphGradient)"
          transform="translate(100 100)"
          initial={{ d: shapes[0] }}
          animate={{ 
            d: shapes[currentShape],
            scale: [1, 1.1, 1],
            rotate: [0, 10, 0]
          }}
          transition={{
            d: { duration: 1.5, ease: 'easeInOut' },
            scale: { duration: 2, repeat: Infinity, ease: 'easeInOut' },
            rotate: { duration: 3, repeat: Infinity, ease: 'easeInOut' }
          }}
        />
      </svg>
      
      {/* Additional glow layer */}
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          background: `radial-gradient(circle, ${colors[0]}40 0%, transparent 70%)`,
          filter: 'blur(20px)'
        }}
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 0.8, 0.5]
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: 'easeInOut'
        }}
      />
    </div>
  );
};
