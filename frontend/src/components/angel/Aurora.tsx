import { motion } from 'framer-motion';

export function Aurora() {
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
      <motion.div
        animate={{
          scale: [1, 1.25, 1],
          rotate: [0, 60, 0],
          opacity: [0.25, 0.5, 0.25],
        }}
        transition={{ duration: 28, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute -top-40 -right-40 w-[38rem] h-[38rem] rounded-full bg-gradient-to-br from-fuchsia-500/30 to-sky-500/30 blur-3xl"
      />
      <motion.div
        animate={{
          scale: [1.1, 0.9, 1.1],
          x: [0, -80, 0],
          y: [0, 40, 0],
          opacity: [0.2, 0.45, 0.2],
        }}
        transition={{ duration: 32, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute -bottom-52 -left-52 w-[44rem] h-[44rem] rounded-full bg-gradient-to-br from-emerald-400/30 to-cyan-500/30 blur-3xl"
      />
      <motion.div
        animate={{
          scale: [1, 1.05, 1],
          x: [0, 50, 0],
          opacity: [0.15, 0.3, 0.15],
        }}
        transition={{ duration: 24, repeat: Infinity, ease: 'linear' }}
        className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[28rem] h-[28rem] rounded-full bg-gradient-to-br from-rose-400/20 to-amber-400/20 blur-3xl"
      />
    </div>
  );
}

export default Aurora;
