/**
 * Aether Easter Eggs & Delight Features
 * Hidden surprises and celebration animations
 */

import { useEffect, useState, useCallback } from 'react';

/**
 * Konami Code Hook
 * ↑ ↑ ↓ ↓ ← → ← → B A
 */
const KONAMI_CODE = [
  'ArrowUp',
  'ArrowUp',
  'ArrowDown',
  'ArrowDown',
  'ArrowLeft',
  'ArrowRight',
  'ArrowLeft',
  'ArrowRight',
  'KeyB',
  'KeyA',
];

export const useKonamiCode = (callback: () => void) => {
  const [keys, setKeys] = useState<string[]>([]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      setKeys((prevKeys) => {
        const newKeys = [...prevKeys, event.code].slice(-KONAMI_CODE.length);
        
        if (newKeys.join(',') === KONAMI_CODE.join(',')) {
          callback();
          return [];
        }
        
        return newKeys;
      });
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [callback]);

  return keys.length;
};

/**
 * Confetti Animation
 */
export const triggerConfetti = () => {
  const colors = [
    'hsl(var(--aether-primary))',
    'hsl(var(--aether-glow))',
    'hsl(var(--aether-accent))',
    '#FFD700',
    '#FF69B4',
  ];

  const confettiCount = 150;
  const container = document.createElement('div');
  container.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 9999;
  `;
  document.body.appendChild(container);

  for (let i = 0; i < confettiCount; i++) {
    const confetti = document.createElement('div');
    const size = Math.random() * 10 + 5;
    const color = colors[Math.floor(Math.random() * colors.length)];
    const startX = Math.random() * window.innerWidth;
    const rotation = Math.random() * 360;
    const duration = Math.random() * 2 + 2;
    const delay = Math.random() * 0.5;

    confetti.style.cssText = `
      position: absolute;
      width: ${size}px;
      height: ${size}px;
      background: ${color};
      top: -20px;
      left: ${startX}px;
      border-radius: ${Math.random() > 0.5 ? '50%' : '0'};
      opacity: ${Math.random() * 0.5 + 0.5};
      transform: rotate(${rotation}deg);
      animation: confetti-fall ${duration}s linear ${delay}s forwards;
    `;

    container.appendChild(confetti);
  }

  // Add CSS animation
  if (!document.getElementById('confetti-styles')) {
    const style = document.createElement('style');
    style.id = 'confetti-styles';
    style.textContent = `
      @keyframes confetti-fall {
        to {
          transform: translateY(${window.innerHeight + 20}px) rotate(720deg);
          opacity: 0;
        }
      }
    `;
    document.head.appendChild(style);
  }

  // Clean up
  setTimeout(() => {
    document.body.removeChild(container);
  }, 5000);
};

/**
 * Achievement System
 */
export type Achievement = {
  id: string;
  title: string;
  description: string;
  icon: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  unlocked: boolean;
  unlockedAt?: Date;
};

const ACHIEVEMENTS: Achievement[] = [
  {
    id: 'first-search',
    title: 'First Steps',
    description: 'Performed your first search',
    icon: '🔍',
    rarity: 'common',
    unlocked: false,
  },
  {
    id: 'power-user',
    title: 'Power User',
    description: 'Performed 100 searches',
    icon: '⚡',
    rarity: 'rare',
    unlocked: false,
  },
  {
    id: 'deal-hunter',
    title: 'Deal Hunter',
    description: 'Saved over $500 with price alerts',
    icon: '💰',
    rarity: 'epic',
    unlocked: false,
  },
  {
    id: 'konami-master',
    title: 'Secret Master',
    description: 'Discovered the Konami Code',
    icon: '🎮',
    rarity: 'legendary',
    unlocked: false,
  },
  {
    id: 'early-bird',
    title: 'Early Bird',
    description: 'Used the app before 6 AM',
    icon: '🌅',
    rarity: 'rare',
    unlocked: false,
  },
  {
    id: 'night-owl',
    title: 'Night Owl',
    description: 'Used the app after midnight',
    icon: '🦉',
    rarity: 'rare',
    unlocked: false,
  },
];

export const useAchievements = () => {
  const [achievements, setAchievements] = useState<Achievement[]>(() => {
    const saved = localStorage.getItem('aether-achievements');
    return saved ? JSON.parse(saved) : ACHIEVEMENTS;
  });

  const unlockAchievement = useCallback((id: string) => {
    setAchievements((prev) => {
      const updated = prev.map((achievement) =>
        achievement.id === id && !achievement.unlocked
          ? { ...achievement, unlocked: true, unlockedAt: new Date() }
          : achievement
      );
      localStorage.setItem('aether-achievements', JSON.stringify(updated));
      return updated;
    });
  }, []);

  const getProgress = useCallback(() => {
    const unlocked = achievements.filter((a) => a.unlocked).length;
    const total = achievements.length;
    return { unlocked, total, percentage: (unlocked / total) * 100 };
  }, [achievements]);

  return {
    achievements,
    unlockAchievement,
    getProgress,
  };
};

/**
 * Seasonal Themes
 */
export const getSeasonalTheme = () => {
  const now = new Date();
  const month = now.getMonth();
  const day = now.getDate();

  // Halloween (October)
  if (month === 9) {
    return {
      name: 'Halloween',
      colors: {
        primary: '30 100% 50%', // Orange
        accent: '270 100% 50%', // Purple
      },
      emoji: '🎃',
    };
  }

  // Christmas (December)
  if (month === 11) {
    return {
      name: 'Christmas',
      colors: {
        primary: '0 100% 50%', // Red
        accent: '120 100% 40%', // Green
      },
      emoji: '🎄',
    };
  }

  // New Year (January 1-7)
  if (month === 0 && day <= 7) {
    return {
      name: 'New Year',
      colors: {
        primary: '45 100% 50%', // Gold
        accent: '240 100% 60%', // Blue
      },
      emoji: '🎊',
    };
  }

  // Valentine's Day (February 14)
  if (month === 1 && day === 14) {
    return {
      name: "Valentine's Day",
      colors: {
        primary: '350 100% 60%', // Pink
        accent: '0 100% 50%', // Red
      },
      emoji: '💝',
    };
  }

  return null;
};

/**
 * Click Counter Easter Egg
 * Triggers celebration after X clicks on a specific element
 */
export const useClickCounter = (threshold = 10, callback?: () => void) => {
  const [count, setCount] = useState(0);

  const handleClick = useCallback(() => {
    setCount((prev) => {
      const newCount = prev + 1;
      if (newCount === threshold) {
        callback?.();
        triggerConfetti();
        return 0;
      }
      return newCount;
    });
  }, [threshold, callback]);

  return { count, handleClick, progress: (count / threshold) * 100 };
};

export default {
  useKonamiCode,
  triggerConfetti,
  useAchievements,
  getSeasonalTheme,
  useClickCounter,
};
