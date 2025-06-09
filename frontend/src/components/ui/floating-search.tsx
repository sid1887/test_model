
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Camera, Mic, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

interface FloatingSearchProps {
  onSearch?: (query: string) => void;
  onImageSearch?: () => void;
  onVoiceSearch?: () => void;
}

const FloatingSearch: React.FC<FloatingSearchProps> = ({
  onSearch,
  onImageSearch,
  onVoiceSearch
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const suggestions = [
    "iPhone 15 Pro Max",
    "MacBook Pro M3",
    "AirPods Pro 2",
    "Samsung Galaxy S24",
    "Sony WH-1000XM5"
  ];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim() && onSearch) {
      onSearch(searchQuery);
      setIsFocused(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setSearchQuery(suggestion);
    onSearch?.(suggestion);
    setIsFocused(false);
  };

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="relative z-30"
      >
        {/* Main Search Container */}
        <motion.div
          className={cn(
            "relative backdrop-blur-xl bg-white/90 dark:bg-black/80 rounded-2xl shadow-2xl border border-white/20 dark:border-white/10 transition-all duration-300",
            isFocused && "ring-2 ring-blue-500/50 shadow-blue-500/25"
          )}
          whileHover={{ y: -2 }}
        >
          <form onSubmit={handleSearch} className="flex items-center p-4">
            <Search className="w-5 h-5 text-muted-foreground mr-3 flex-shrink-0" />
            
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setTimeout(() => setIsFocused(false), 200)}
              placeholder="Search for products, brands, or upload an image..."
              className="flex-1 border-0 bg-transparent text-lg placeholder:text-muted-foreground focus:ring-0 focus:outline-none"
            />

            <div className="flex items-center gap-2 ml-3 flex-shrink-0">
              <motion.button
                type="button"
                onClick={onImageSearch}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="p-2 rounded-xl bg-gradient-to-br from-green-400 to-blue-500 text-white shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <Camera className="w-4 h-4" />
              </motion.button>

              <motion.button
                type="button"
                onClick={onVoiceSearch}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                className="p-2 rounded-xl bg-gradient-to-br from-purple-400 to-pink-500 text-white shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <Mic className="w-4 h-4" />
              </motion.button>
            </div>
          </form>
        </motion.div>

        {/* Search Suggestions */}
        <AnimatePresence>
          {isFocused && (
            <>
              {/* Backdrop */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-10"
                onClick={() => setIsFocused(false)}
              />
              
              {/* Suggestions Panel */}
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="absolute top-full left-0 right-0 mt-2 backdrop-blur-xl bg-white/95 dark:bg-black/90 rounded-xl shadow-2xl border border-white/20 dark:border-white/10 overflow-hidden z-50"
              >
                <div className="p-2">
                  <div className="text-xs font-medium text-muted-foreground px-3 py-2">Popular Searches</div>
                  {suggestions.map((suggestion, index) => (
                    <motion.button
                      key={suggestion}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="w-full text-left px-3 py-2 rounded-lg hover:bg-accent transition-colors duration-200 flex items-center gap-3"
                    >
                      <Search className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      <span>{suggestion}</span>
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export { FloatingSearch };
