'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MagnifyingGlassIcon, XMarkIcon, MicrophoneIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  placeholder?: string;
  suggestions?: string[];
  onSuggestionClick?: (suggestion: string) => void;
  loading?: boolean;
  variant?: 'default' | 'glass' | 'floating';
  size?: 'sm' | 'md' | 'lg';
  showVoiceSearch?: boolean;
  onVoiceSearch?: () => void;
  className?: string;
}

const variantStyles = {
  default: 'bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700',
  glass: 'glass backdrop-blur-xl border border-white/20 dark:border-gray-700/20',
  floating: 'bg-white dark:bg-gray-900 shadow-2xl border border-gray-200 dark:border-gray-800',
};

const sizeStyles = {
  sm: 'h-10 text-sm',
  md: 'h-12 text-base',
  lg: 'h-14 text-lg',
};

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search for products...',
  suggestions = [],
  onSuggestionClick,
  loading = false,
  variant = 'glass',
  size = 'lg',
  showVoiceSearch = true,
  onVoiceSearch,
  className,
}) => {
  const [isFocused, setIsFocused] = React.useState(false);
  const [showSuggestions, setShowSuggestions] = React.useState(false);
  const searchRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSubmit) {
      onSubmit();
    }
    setShowSuggestions(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    setShowSuggestions(newValue.length > 0 && suggestions.length > 0);
  };

  const handleSuggestionClick = (suggestion: string) => {
    onChange(suggestion);
    setShowSuggestions(false);
    if (onSuggestionClick) {
      onSuggestionClick(suggestion);
    }
  };

  const clearSearch = () => {
    onChange('');
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
        setIsFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div ref={searchRef} className={cn('relative w-full max-w-2xl mx-auto', className)}>
      <motion.form
        onSubmit={handleSubmit}
        className="relative"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      >
        <motion.div
          className={cn(
            'relative flex items-center rounded-2xl transition-all duration-300',
            variantStyles[variant],
            sizeStyles[size],
            {
              'ring-2 ring-primary-500 ring-opacity-50 shadow-glow-primary': isFocused,
              'shadow-lg': variant === 'floating',
            }
          )}
          animate={{
            scale: isFocused ? 1.02 : 1,
          }}
          transition={{ duration: 0.2 }}
        >
          {/* Search Icon */}
          <motion.div
            className="absolute left-4 flex items-center justify-center"
            animate={{
              scale: loading ? 0 : 1,
              rotate: loading ? 180 : 0,
            }}
            transition={{ duration: 0.3 }}
          >
            {loading ? (
              <motion.div
                className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              />
            ) : (
              <MagnifyingGlassIcon className="w-5 h-5 text-gray-400" />
            )}
          </motion.div>

          {/* Input Field */}
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={handleInputChange}
            onFocus={() => {
              setIsFocused(true);
              setShowSuggestions(value.length > 0 && suggestions.length > 0);
            }}
            placeholder={placeholder}
            className={cn(
              'flex-1 px-12 bg-transparent outline-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400',
              sizeStyles[size]
            )}
          />

          {/* Clear Button */}
          <AnimatePresence>
            {value && (
              <motion.button
                type="button"
                onClick={clearSearch}
                className="absolute right-16 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <XMarkIcon className="w-4 h-4" />
              </motion.button>
            )}
          </AnimatePresence>

          {/* Voice Search Button */}
          {showVoiceSearch && (
            <motion.button
              type="button"
              onClick={onVoiceSearch}
              className="absolute right-4 p-2 text-gray-400 hover:text-primary-500 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              transition={{ duration: 0.2 }}
            >
              <MicrophoneIcon className="w-5 h-5" />
            </motion.button>
          )}
        </motion.div>
      </motion.form>

      {/* Suggestions Dropdown */}
      <AnimatePresence>
        {showSuggestions && suggestions.length > 0 && (
          <motion.div
            className={cn(
              'absolute top-full left-0 right-0 mt-2 py-2 rounded-xl shadow-2xl border z-50',
              variantStyles[variant]
            )}
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
          >
            {suggestions.map((suggestion, index) => (
              <motion.button
                key={suggestion}
                type="button"
                onClick={() => handleSuggestionClick(suggestion)}
                className="w-full px-4 py-3 text-left text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex items-center space-x-3"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
                whileHover={{ x: 4 }}
              >
                <MagnifyingGlassIcon className="w-4 h-4 text-gray-400" />
                <span>{suggestion}</span>
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
