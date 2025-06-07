'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from './theme-provider';
import { SunIcon, MoonIcon, ComputerDesktopIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

interface ThemeSwitcherProps {
  variant?: 'default' | 'compact' | 'floating';
  showLabels?: boolean;
  className?: string;
}

export const ThemeSwitcher: React.FC<ThemeSwitcherProps> = ({
  variant = 'default',
  showLabels = true,
  className,
}) => {
  const { theme, setTheme, actualTheme } = useTheme();

  const themes = [
    {
      name: 'light',
      label: 'Light',
      icon: SunIcon,
      description: 'Light theme',
    },
    {
      name: 'dark',
      label: 'Dark',
      icon: MoonIcon,
      description: 'Dark theme',
    },
    {
      name: 'system',
      label: 'System',
      icon: ComputerDesktopIcon,
      description: 'Follow system theme',
    },
  ] as const;

  if (variant === 'compact') {
    return (
      <motion.button
        onClick={() => {
          const nextTheme = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light';
          setTheme(nextTheme);
        }}
        className={cn(
          'relative p-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-300',
          className
        )}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        title={`Current theme: ${theme}`}
      >
        <motion.div
          key={theme}
          initial={{ rotate: -180, opacity: 0 }}
          animate={{ rotate: 0, opacity: 1 }}
          exit={{ rotate: 180, opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          {theme === 'light' && <SunIcon className="w-5 h-5" />}
          {theme === 'dark' && <MoonIcon className="w-5 h-5" />}
          {theme === 'system' && <ComputerDesktopIcon className="w-5 h-5" />}
        </motion.div>
      </motion.button>
    );
  }

  if (variant === 'floating') {
    return (
      <motion.div
        className={cn(
          'fixed bottom-6 right-6 z-50 glass rounded-full p-2 shadow-2xl',
          className
        )}
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      >
        <div className="flex space-x-1">
          {themes.map(({ name, icon: Icon }) => (
            <motion.button
              key={name}
              onClick={() => setTheme(name)}
              className={cn(
                'p-2 rounded-full transition-all duration-300',
                theme === name
                  ? 'bg-primary-500 text-white shadow-glow-primary'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              )}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              title={`Switch to ${name} theme`}
            >
              <Icon className="w-4 h-4" />
            </motion.button>
          ))}
        </div>
      </motion.div>
    );
  }

  return (
    <div className={cn('flex items-center space-x-1', className)}>
      {themes.map(({ name, label, icon: Icon, description }) => (
        <motion.button
          key={name}
          onClick={() => setTheme(name)}
          className={cn(
            'flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-300',
            theme === name
              ? 'bg-primary-500 text-white shadow-glow-primary'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
          )}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          title={description}
        >
          <motion.div
            animate={{
              rotate: theme === name ? 360 : 0,
            }}
            transition={{ duration: 0.5 }}
          >
            <Icon className="w-4 h-4" />
          </motion.div>
          {showLabels && <span>{label}</span>}
        </motion.button>
      ))}
    </div>
  );
};
