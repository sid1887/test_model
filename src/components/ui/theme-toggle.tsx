
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon, Monitor, ChevronDown } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import { useTranslation } from '@/i18n';
import { useAccessibility } from '@/hooks/useAccessibility';

const ThemeToggle: React.FC = () => {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const { t } = useTranslation();
  const { getAriaProps, getKeyboardProps } = useAccessibility();
  const [isOpen, setIsOpen] = useState(false);

  const themes = [
    { key: 'light' as const, icon: Sun, label: 'Light' },
    { key: 'dark' as const, icon: Moon, label: 'Dark' },
    { key: 'system' as const, icon: Monitor, label: 'System' }
  ];

  const currentTheme = themes.find(t => t.key === theme) || themes[0];

  return (
    <div className="relative z-50">
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="relative p-3 rounded-xl bg-gradient-to-br from-orange-400 to-purple-600 text-white shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden flex items-center gap-2"
        {...getAriaProps(t('accessibility.themeToggle'), isOpen, 'theme-dropdown')}
        {...getKeyboardProps(() => setIsOpen(!isOpen))}
      >
        <motion.div
          initial={false}
          animate={{ 
            rotate: resolvedTheme === 'dark' ? 180 : 0,
            scale: resolvedTheme === 'dark' ? 0.8 : 1
          }}
          transition={{ type: "spring", stiffness: 200, damping: 20 }}
        >
          <currentTheme.icon className="w-5 h-5" />
        </motion.div>
        <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        
        {/* Animated background */}
        <motion.div
          className="absolute inset-0 bg-gradient-to-br from-purple-600 to-blue-500"
          initial={{ opacity: 0 }}
          animate={{ opacity: resolvedTheme === 'dark' ? 1 : 0 }}
          transition={{ duration: 0.3 }}
        />
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />
            
            {/* Dropdown Menu */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="absolute top-full right-0 mt-2 bg-popover border border-border rounded-lg shadow-lg py-1 z-50 min-w-[120px] backdrop-blur-md"
              id="theme-dropdown"
            >
              {themes.map((themeOption) => (
                <motion.button
                  key={themeOption.key}
                  onClick={() => {
                    setTheme(themeOption.key);
                    setIsOpen(false);
                  }}
                  whileHover={{ backgroundColor: 'hsl(var(--accent))' }}
                  className="w-full flex items-center gap-3 px-3 py-2 text-sm text-popover-foreground hover:bg-accent transition-colors"
                >
                  <themeOption.icon className="w-4 h-4" />
                  <span>{themeOption.label}</span>
                  {theme === themeOption.key && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="ml-auto w-2 h-2 bg-primary rounded-full"
                    />
                  )}
                </motion.button>
              ))}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export { ThemeToggle };
