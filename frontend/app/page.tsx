'use client';

import React, { useState, useRef, useCallback } from 'react';
import axios from 'axios';
import { MagnifyingGlassIcon, PhotoIcon, ArrowUpTrayIcon } from '@heroicons/react/24/outline';

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('text'); // 'text' or 'image'
  const [selectedImage, setSelectedImage] = useState(null);
  const fileInputRef = useRef(null);

  // Text search function
  const handleTextSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.post('/api/v1/analysis/search-products', {
        query: searchQuery,
        limit: 10,
        min_similarity: 0.7
      });
      
      setSearchResults(response.data.results || []);
    } catch (err) {
      setError('Search failed. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Image search function
  const handleImageSearch = async (file) => {
    if (!file) return;
    
    setLoading(true);
    setError('');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await axios.post('/api/v1/analysis/search-by-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        params: {
          limit: 10,
          min_similarity: 0.7
        }
      });
      
      setSearchResults(response.data.results || []);
    } catch (err) {
      setError('Image search failed. Please try again.');
      console.error('Image search error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle file selection
  const handleFileSelect = useCallback((event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      handleImageSearch(file);
    }
  }, []);

  // Drag and drop handlers
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedImage(file);
      handleImageSearch(file);
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Cumpair</h1>
              <span className="ml-2 text-sm text-gray-500">AI Price Comparison</span>
            </div>
            <div className="flex items-center space-x-4">
              <button className="text-gray-500 hover:text-gray-700">
                <MagnifyingGlassIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Search Section */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Find the Best Prices Instantly
            </h2>
            <p className="text-gray-600 text-lg">
              Search by text or upload an image to compare prices across multiple platforms
            </p>
          </div>

          {/* Search Tabs */}
          <div className="flex justify-center mb-6">
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setActiveTab('text')}
                className={`px-6 py-2 rounded-md font-medium transition-colors ${
                  activeTab === 'text'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Text Search
              </button>
              <button
                onClick={() => setActiveTab('image')}
                className={`px-6 py-2 rounded-md font-medium transition-colors ${
                  activeTab === 'image'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Image Search
              </button>
            </div>
          </div>

          {/* Text Search */}
          {activeTab === 'text' && (
            <div className="space-y-4">
              <div className="flex space-x-4">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleTextSearch()}
                  placeholder="Enter product name, brand, or description..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={handleTextSearch}
                  disabled={loading || !searchQuery.trim()}
                  className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  <MagnifyingGlassIcon className="h-5 w-5" />
                  <span>{loading ? 'Searching...' : 'Search'}</span>
                </button>
              </div>
            </div>
          )}

          {/* Image Search */}
          {activeTab === 'image' && (
            <div className="space-y-4">
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <PhotoIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">
                  Drag and drop an image, or click to select
                </p>
                <p className="text-sm text-gray-500">
                  Supports JPG, PNG, WebP up to 10MB
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
              
              {selectedImage && (
                <div className="text-center">
                  <p className="text-sm text-gray-600">
                    Selected: {selectedImage.name}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600">{error}</p>
            </div>
          )}
        </div>

        {/* Results Section */}
        {(loading || searchResults.length > 0) && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">
              Search Results
            </h3>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">Searching products...</span>
              </div>
            ) : (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {searchResults.map((result, index) => (
                  <div key={index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="aspect-w-1 aspect-h-1 mb-4">
                      <div className="bg-gray-100 rounded-lg flex items-center justify-center">
                        <PhotoIcon className="h-8 w-8 text-gray-400" />
                      </div>
                    </div>
                    
                    <h4 className="font-medium text-gray-900 mb-2 line-clamp-2">
                      {result.title || 'Product Title'}
                    </h4>
                    
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg font-bold text-green-600">
                        ${result.price_usd || 'N/A'}
                      </span>
                      <span className="text-sm text-gray-500 capitalize">
                        {result.site}
                      </span>
                    </div>
                    
                    {result.similarity && (
                      <div className="mb-3">
                        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                          <span>Match</span>
                          <span>{Math.round(result.similarity * 100)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1">
                          <div 
                            className="bg-blue-600 h-1 rounded-full" 
                            style={{ width: `${result.similarity * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    )}
                    
                    <button 
                      onClick={() => window.open(result.url, '_blank')}
                      className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors text-sm"
                    >
                      View Product
                    </button>
                  </div>
                ))}
              </div>
            )}

            {!loading && searchResults.length === 0 && (
              <div className="text-center py-12">
                <PhotoIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No products found. Try a different search term.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
