/**
 * Unified App Layout with Aether Design System
 * Provides consistent navigation, header, sidebar, and transitions
 */

import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  Search,
  Bell,
  List,
  BarChart3,
  Brain,
  ImageIcon,
  Mic,
  ChevronLeft,
  Menu,
  X,
  Sparkles,
  User
} from 'lucide-react';
import { AuroraEnhanced } from '@/components/angel/AuroraEnhanced';
import { AetherButton } from '@/components/angel/AetherButton';

interface AppLayoutProps {
  children: React.ReactNode;
}

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const navItems: NavItem[] = [
  {
    path: '/',
    label: 'Home',
    icon: <Home className="h-5 w-5" />,
    description: 'Dashboard and overview'
  },
  {
    path: '/search',
    label: 'Search',
    icon: <Search className="h-5 w-5" />,
    description: 'AI-powered product search'
  },
  {
    path: '/alerts',
    label: 'Price Alerts',
    icon: <Bell className="h-5 w-5" />,
    description: 'Monitor price changes'
  },
  {
    path: '/lists',
    label: 'Smart Lists',
    icon: <List className="h-5 w-5" />,
    description: 'Shopping list management'
  },
  {
    path: '/analytics',
    label: 'Analytics',
    icon: <BarChart3 className="h-5 w-5" />,
    description: 'Trends and insights'
  },
  {
    path: '/ai-insights',
    label: 'AI Insights',
    icon: <Brain className="h-5 w-5" />,
    description: 'AI-powered analysis'
  }
];

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Get current page info
  const currentNav = navItems.find(item => item.path === location.pathname);
  const isHomePage = location.pathname === '/';

  // Handle scroll for header effect
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close sidebar on navigation
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  const handleBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen relative overflow-x-hidden">
      {/* Aurora Background */}
      <div className="fixed inset-0 z-0">
        <AuroraEnhanced />
      </div>

      {/* App Container */}
      <div className="relative z-10">
        {/* Header */}
        <motion.header
          className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
            scrolled 
              ? 'bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl shadow-lg' 
              : 'bg-transparent'
          }`}
          initial={{ y: -100 }}
          animate={{ y: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              {/* Left: Logo & Back Button */}
              <div className="flex items-center gap-4">
                {!isHomePage && (
                  <motion.button
                    onClick={handleBack}
                    className="p-2 rounded-xl bg-white/10 backdrop-blur-sm hover:bg-white/20 
                             border border-white/20 transition-all duration-300 group"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <ChevronLeft className="h-5 w-5 text-gray-700 dark:text-white 
                                           group-hover:text-blue-600 transition-colors" />
                  </motion.button>
                )}
                
                <Link to="/" className="flex items-center gap-3 group">
                  <div className="relative">
                    <motion.div
                      className="absolute -inset-2 bg-gradient-to-r from-blue-500 to-purple-600 
                                 rounded-full opacity-0 group-hover:opacity-100 blur-xl transition-opacity"
                      animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.5, 0.8, 0.5]
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: 'easeInOut'
                      }}
                    />
                    <Sparkles className="h-8 w-8 text-blue-600 dark:text-blue-400 relative z-10" />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 
                                   bg-clip-text text-transparent">
                      Cumpair
                    </h1>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      God Engine
                    </p>
                  </div>
                </Link>
              </div>

              {/* Center: Breadcrumbs */}
              {!isHomePage && currentNav && (
                <motion.div
                  className="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl 
                             bg-white/10 backdrop-blur-sm border border-white/20"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                >
                  <div className="text-blue-600 dark:text-blue-400">
                    {currentNav.icon}
                  </div>
                  <span className="text-sm font-medium text-gray-700 dark:text-white">
                    {currentNav.label}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    • {currentNav.description}
                  </span>
                </motion.div>
              )}

              {/* Right: Actions & Menu */}
              <div className="flex items-center gap-3">
                {/* Quick Actions */}
                <div className="hidden lg:flex items-center gap-2">
                  <AetherButton
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/search')}
                  >
                    <Search className="h-4 w-4" />
                    Search
                  </AetherButton>
                  <AetherButton
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/search?mode=image')}
                  >
                    <ImageIcon className="h-4 w-4" />
                  </AetherButton>
                  <AetherButton
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/search?mode=voice')}
                  >
                    <Mic className="h-4 w-4" />
                  </AetherButton>
                </div>

                {/* User Menu */}
                <motion.button
                  className="p-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 
                             text-white hover:shadow-lg transition-all duration-300"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <User className="h-5 w-5" />
                </motion.button>

                {/* Mobile Menu Toggle */}
                <motion.button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="lg:hidden p-2 rounded-xl bg-white/10 backdrop-blur-sm 
                             hover:bg-white/20 border border-white/20 transition-all"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {sidebarOpen ? (
                    <X className="h-5 w-5 text-gray-700 dark:text-white" />
                  ) : (
                    <Menu className="h-5 w-5 text-gray-700 dark:text-white" />
                  )}
                </motion.button>
              </div>
            </div>
          </div>
        </motion.header>

        {/* Sidebar Navigation */}
        <AnimatePresence>
          {sidebarOpen && (
            <>
              {/* Backdrop */}
              <motion.div
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setSidebarOpen(false)}
              />

              {/* Sidebar */}
              <motion.aside
                className="fixed top-0 right-0 h-full w-80 bg-white/90 dark:bg-gray-900/90 
                           backdrop-blur-xl shadow-2xl z-50 lg:hidden overflow-y-auto"
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              >
                <div className="p-6">
                  <div className="flex items-center justify-between mb-8">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                      Navigation
                    </h2>
                    <button
                      onClick={() => setSidebarOpen(false)}
                      className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 
                                 transition-colors"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  {/* Navigation Items */}
                  <nav className="space-y-2">
                    {navItems.map((item, index) => {
                      const isActive = location.pathname === item.path;
                      return (
                        <motion.div
                          key={item.path}
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                        >
                          <Link
                            to={item.path}
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl 
                                       transition-all duration-300 group ${
                              isActive
                                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                                : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                            }`}
                          >
                            <div className={`transition-transform duration-300 ${
                              isActive ? 'scale-110' : 'group-hover:scale-110'
                            }`}>
                              {item.icon}
                            </div>
                            <div className="flex-1">
                              <div className="font-medium">{item.label}</div>
                              <div className={`text-xs ${
                                isActive ? 'text-white/80' : 'text-gray-500 dark:text-gray-400'
                              }`}>
                                {item.description}
                              </div>
                            </div>
                            {isActive && (
                              <motion.div
                                className="h-2 w-2 rounded-full bg-white"
                                layoutId="activeIndicator"
                              />
                            )}
                          </Link>
                        </motion.div>
                      );
                    })}
                  </nav>

                  {/* Quick Stats */}
                  <div className="mt-8 p-4 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-600/10 
                                  border border-blue-500/20">
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      Quick Stats
                    </h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Active Alerts</span>
                        <span className="font-bold text-blue-600">12</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Smart Lists</span>
                        <span className="font-bold text-purple-600">5</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Searches Today</span>
                        <span className="font-bold text-green-600">34</span>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <main className="pt-16">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Floating Action Button (Mobile) */}
        <motion.div
          className="fixed bottom-6 right-6 lg:hidden z-40"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.5, type: 'spring', stiffness: 300, damping: 20 }}
        >
          <motion.button
            onClick={() => navigate('/search')}
            className="p-4 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 
                       text-white shadow-2xl hover:shadow-blue-500/50 transition-all"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            animate={{
              boxShadow: [
                '0 10px 40px rgba(59, 130, 246, 0.3)',
                '0 10px 60px rgba(147, 51, 234, 0.5)',
                '0 10px 40px rgba(59, 130, 246, 0.3)'
              ]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut'
            }}
          >
            <Search className="h-6 w-6" />
          </motion.button>
        </motion.div>
      </div>
    </div>
  );
};
