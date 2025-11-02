import { motion } from 'framer-motion';

/**
 * Enhanced Aurora Background - Aether Design System
 * Multi-layer animated gradient orbs with noise texture overlay
 */
export function AuroraEnhanced() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none" style={{ zIndex: 'var(--z-background, -1)' }}>
      {/* Noise Texture Overlay for Depth */}
      <div 
        className="absolute inset-0 opacity-[0.015] dark:opacity-[0.025]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' /%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat'
        }}
      />

      {/* Primary Aether Orb - Top Right */}
      <motion.div
        className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full blur-[100px] opacity-40"
        style={{
          background: 'linear-gradient(135deg, hsl(270 80% 45%), hsl(250 85% 60%), hsl(200 90% 55%))'
        }}
        animate={{
          scale: [1, 1.3, 1],
          rotate: [0, 180, 360],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "linear"
        }}
      />

      {/* Secondary Aether Orb - Bottom Left */}
      <motion.div
        className="absolute -bottom-40 -left-40 w-[700px] h-[700px] rounded-full blur-[120px] opacity-40"
        style={{
          background: 'linear-gradient(135deg, hsl(250 85% 60%), hsl(200 90% 55%), hsl(270 80% 45%))'
        }}
        animate={{
          scale: [1.3, 1, 1.3],
          rotate: [360, 180, 0],
          opacity: [0.35, 0.55, 0.35],
        }}
        transition={{
          duration: 30,
          repeat: Infinity,
          ease: "linear"
        }}
      />

      {/* Accent Orb - Floating Center */}
      <motion.div
        className="absolute top-1/2 left-1/2 w-96 h-96 rounded-full blur-3xl opacity-20"
        style={{
          background: 'radial-gradient(circle, hsl(15 90% 60%), transparent 70%)'
        }}
        animate={{
          scale: [1, 1.2, 1],
          x: [-200, 100, -200],
          y: [-100, 50, -100],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      {/* Glow Orb - Top Quarter */}
      <motion.div
        className="absolute top-1/4 right-1/4 w-64 h-64 rounded-full blur-[80px] opacity-25"
        style={{
          background: 'radial-gradient(circle, hsl(250 85% 60%), transparent 70%)'
        }}
        animate={{
          y: [0, -30, 0],
          x: [0, 20, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      {/* Subtle Ambient Orb - Bottom Quarter */}
      <motion.div
        className="absolute bottom-1/3 left-1/3 w-80 h-80 rounded-full blur-[90px] opacity-15"
        style={{
          background: 'radial-gradient(circle, hsl(200 90% 55%), transparent 70%)'
        }}
        animate={{
          scale: [0.9, 1.15, 0.9],
          rotate: [0, 120, 0],
        }}
        transition={{
          duration: 35,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
    </div>
  );
}

export default AuroraEnhanced;
