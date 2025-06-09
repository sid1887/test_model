'use client';

import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { 
  MagnifyingGlassIcon, 
  PhotoIcon, 
  ArrowUpTrayIcon,
  SparklesIcon,
  HeartIcon,
  ShareIcon,
  EyeIcon,
  ShoppingCartIcon,
  CameraIcon,
  MicrophoneIcon,
  XMarkIcon,
  CheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';

// UI Components
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { SearchBar } from './components/ui/search-bar';
import { ThemeSwitcher } from './components/ui/theme-switcher';
import { Skeleton, ProductCardSkeleton, SearchResultsSkeleton } from './components/ui/skeleton';

// Utils
import { cn, formatPrice, formatRelativeTime } from './lib/utils';

interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  image_url?: string;
  similarity_score?: number;
  created_at: string;
  is_processed: boolean;
}

interface SearchResult {
  id: number;
  title: string;
  description: string;
  price: number;
  image_url?: string;
  similarity_score: number;
  metadata?: any;
}

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'text' | 'image'>('text');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const [recentSearches, setRecentSearches] = useState<string[]>([
    'iPhone 15',
    'Nike Air Force 1',
    'MacBook Pro',
    'AirPods Pro',
    'PlayStation 5'
  ]);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  // Enhanced text search function
  const handleTextSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post('/api/v1/analysis/search-products', {
        query: searchQuery,
        limit: 12,
        min_similarity: 0.7
      });
      
      setSearchResults(response.data.results || []);
      
      // Add to recent searches
      setRecentSearches(prev => {
        const filtered = prev.filter(item => item !== searchQuery);
        return [searchQuery, ...filtered].slice(0, 5);
      });
    } catch (err) {
      setError('Search failed. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  // Enhanced image search function
  const handleImageSearch = useCallback(async (file: File) => {
    if (!file) return;
    
    setLoading(true);
    setError('');
    setUploadProgress(0);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post('/api/v1/analysis/search-by-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = progressEvent.total 
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress(progress);
        },
      });
      
      setSearchResults(response.data.results || []);
    } catch (err) {
      setError('Image search failed. Please try again.');
      console.error('Image search error:', err);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  }, []);

  // File handling
  const handleFileSelect = useCallback((file: File) => {
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      handleImageSearch(file);
    }
  }, [handleImageSearch]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  // Drag and drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find(file => file.type.startsWith('image/'));
    
    if (imageFile) {
      handleFileSelect(imageFile);
    }
  };

  // Favorites
  const toggleFavorite = (id: number) => {
    setFavorites(prev => {
      const newFavorites = new Set(prev);
      if (newFavorites.has(id)) {
        newFavorites.delete(id);
      } else {
        newFavorites.add(id);
      }
      return newFavorites;
    });
  };

  // Voice search placeholder
  const handleVoiceSearch = () => {
    // Implement voice search functionality
    console.log('Voice search triggered');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 transition-all duration-500">
      {/* Enhanced Header */}
      <motion.header 
        className="glass sticky top-0 z-50 border-b border-white/20 dark:border-gray-700/20"
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <motion.div 
              className="flex items-center space-x-3"
              whileHover={{ scale: 1.05 }}
              transition={{ duration: 0.2 }}
            >
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center">
                <SparklesIcon className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gradient">Cumpair</h1>
            </motion.div>
            
            <ThemeSwitcher variant="compact" />
          </div>
        </div>
      </motion.header>

      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <motion.section 
          className="text-center py-12 space-y-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="space-y-4">
            <motion.h2 
              className="text-4xl md:text-6xl font-bold text-gradient"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              Find. Compare. Save.
            </motion.h2>
            <motion.p 
              className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              Discover the best prices across the web with AI-powered product recognition and smart comparison
            </motion.p>
          </div>

          {/* Enhanced Search Interface */}
          <motion.div 
            className="space-y-6"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            {/* Tab Switcher */}
            <div className="flex justify-center">
              <div className="glass rounded-2xl p-1 flex space-x-1">
                {[
                  { id: 'text', label: 'Text Search', icon: MagnifyingGlassIcon },
                  { id: 'image', label: 'Image Search', icon: CameraIcon }
                ].map(({ id, label, icon: Icon }) => (
                  <motion.button
                    key={id}
                    onClick={() => setActiveTab(id as 'text' | 'image')}
                    className={cn(
                      'flex items-center space-x-2 px-6 py-3 rounded-xl font-medium transition-all duration-300',
                      activeTab === id
                        ? 'bg-primary-500 text-white shadow-glow-primary'
                        : 'text-gray-600 dark:text-gray-300 hover:bg-white/50 dark:hover:bg-gray-800/50'
                    )}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{label}</span>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Search Content */}
            <AnimatePresence mode="wait">
              {activeTab === 'text' ? (
                <motion.div
                  key="text-search"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                >
                  <SearchBar
                    value={searchQuery}
                    onChange={setSearchQuery}
                    onSubmit={handleTextSearch}
                    suggestions={recentSearches}
                    onSuggestionClick={(suggestion) => {
                      setSearchQuery(suggestion);
                      setTimeout(handleTextSearch, 100);
                    }}
                    loading={loading}
                    variant="glass"
                    size="lg"
                    showVoiceSearch={true}
                    onVoiceSearch={handleVoiceSearch}
                    className="max-w-3xl mx-auto"
                  />
                </motion.div>
              ) : (
                <motion.div
                  key="image-search"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                  className="max-w-2xl mx-auto"
                >
                  {/* Image Upload Area */}
                  <div
                    ref={dropZoneRef}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    className="glass rounded-2xl p-8 border-2 border-dashed border-primary-300 dark:border-primary-700 hover:border-primary-500 transition-all duration-300 cursor-pointer"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleFileInputChange}
                      className="hidden"
                    />
                    
                    {previewUrl ? (
                      <motion.div 
                        className="space-y-4"
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                      >
                        <div className="relative max-w-xs mx-auto">
                          <img
                            src={previewUrl}
                            alt="Preview"
                            className="w-full h-48 object-cover rounded-xl"
                          />
                          <motion.button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedImage(null);
                              setPreviewUrl('');
                              URL.revokeObjectURL(previewUrl);
                            }}
                            className="absolute -top-2 -right-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                          >
                            <XMarkIcon className="w-4 h-4" />
                          </motion.button>
                        </div>
                        
                        {uploadProgress > 0 && uploadProgress < 100 && (
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <motion.div
                              className="bg-primary-500 h-2 rounded-full"
                              initial={{ width: 0 }}
                              animate={{ width: `${uploadProgress}%` }}
                              transition={{ duration: 0.3 }}
                            />
                          </div>
                        )}
                      </motion.div>
                    ) : (
                      <motion.div 
                        className="text-center space-y-4"
                        whileHover={{ scale: 1.02 }}
                      >
                        <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-2xl flex items-center justify-center mx-auto">
                          <PhotoIcon className="w-8 h-8 text-primary-500" />
                        </div>
                        <div>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">
                            Upload or drag an image
                          </p>
                          <p className="text-gray-600 dark:text-gray-400">
                            PNG, JPG, WEBP up to 10MB
                          </p>
                        </div>
                        <Button variant="outline" size="lg" className="mx-auto">
                          <ArrowUpTrayIcon className="w-5 h-5 mr-2" />
                          Choose File
                        </Button>
                      </motion.div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.section>

        {/* Error Message */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.95 }}
              className="max-w-2xl mx-auto mb-8"
            >
              <div className="glass rounded-xl p-4 border-l-4 border-red-500 flex items-center space-x-3">
                <ExclamationTriangleIcon className="w-5 h-5 text-red-500 flex-shrink-0" />
                <p className="text-red-700 dark:text-red-300">{error}</p>
                <button
                  onClick={() => setError('')}
                  className="ml-auto text-red-500 hover:text-red-700 transition-colors"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Search Results */}
        <AnimatePresence>
          {(loading || searchResults.length > 0) && (
            <motion.section
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 40 }}
              transition={{ duration: 0.5 }}
              className="space-y-6"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {loading ? 'Searching...' : `Found ${searchResults.length} results`}
                </h3>
                
                {!loading && searchResults.length > 0 && (
                  <motion.div 
                    className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    <CheckIcon className="w-4 h-4 text-green-500" />
                    <span>Results powered by AI</span>
                  </motion.div>
                )}
              </div>

              {loading ? (
                <SearchResultsSkeleton count={6} />
              ) : (
                <motion.div 
                  className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.5, staggerChildren: 0.1 }}
                >
                  {searchResults.map((result, index) => (
                    <motion.div
                      key={result.id}
                      initial={{ opacity: 0, y: 20, scale: 0.9 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      whileHover={{ y: -4 }}
                    >
                      <Card variant="glass" hover="lift" className="h-full group">
                        <CardContent className="p-0">
                          {/* Image */}
                          <div className="relative overflow-hidden rounded-t-xl">
                            {result.image_url ? (
                              <img
                                src={result.image_url}
                                alt={result.title}
                                className="w-full h-48 object-cover group-hover:scale-110 transition-transform duration-500"
                              />
                            ) : (
                              <div className="w-full h-48 bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
                                <PhotoIcon className="w-12 h-12 text-gray-400" />
                              </div>
                            )}
                            
                            {/* Overlay Actions */}
                            <div className="absolute top-2 right-2 flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <motion.button
                                onClick={() => toggleFavorite(result.id)}
                                className="w-8 h-8 bg-white/90 dark:bg-gray-900/90 rounded-full flex items-center justify-center hover:scale-110 transition-transform"
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                              >
                                {favorites.has(result.id) ? (
                                  <HeartSolidIcon className="w-4 h-4 text-red-500" />
                                ) : (
                                  <HeartIcon className="w-4 h-4 text-gray-600" />
                                )}
                              </motion.button>
                              
                              <motion.button
                                className="w-8 h-8 bg-white/90 dark:bg-gray-900/90 rounded-full flex items-center justify-center hover:scale-110 transition-transform"
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                              >
                                <ShareIcon className="w-4 h-4 text-gray-600" />
                              </motion.button>
                            </div>
                            
                            {/* Similarity Score */}
                            {result.similarity_score && (
                              <div className="absolute bottom-2 left-2">
                                <div className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                                  {Math.round(result.similarity_score * 100)}% match
                                </div>
                              </div>
                            )}
                          </div>
                          
                          {/* Content */}
                          <div className="p-4 space-y-3">
                            <h4 className="font-semibold text-gray-900 dark:text-white line-clamp-2 group-hover:text-primary-500 transition-colors">
                              {result.title}
                            </h4>
                            
                            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                              {result.description}
                            </p>
                            
                            <div className="flex items-center justify-between">
                              <span className="text-2xl font-bold text-primary-500">
                                {formatPrice(result.price)}
                              </span>
                              
                              <Button size="sm" variant="outline" className="group-hover:bg-primary-500 group-hover:text-white transition-all">
                                <ShoppingCartIcon className="w-4 h-4 mr-1" />
                                View
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </motion.section>
          )}
        </AnimatePresence>

        {/* Empty State */}
        {!loading && searchResults.length === 0 && !error && (searchQuery || selectedImage) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-12 space-y-4"
          >
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-2xl flex items-center justify-center mx-auto">
              <MagnifyingGlassIcon className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
              No results found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
              Try adjusting your search terms or uploading a different image for better results.
            </p>
          </motion.div>
        )}
      </main>

      {/* Floating Theme Switcher */}
      <ThemeSwitcher variant="floating" showLabels={false} />
    </div>
  );
}
