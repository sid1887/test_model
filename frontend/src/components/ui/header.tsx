/**
 * Header Component
 * Unified navigation header with working links and dynamic Retailers dropdown
 */

import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Menu, 
  X, 
  Search, 
  Bell, 
  List, 
  BarChart3, 
  Store, 
  ChevronDown,
  Home,
  Moon,
  Sun
} from 'lucide-react';
import { Button } from './button';
import { useTheme } from '@/contexts/ThemeContext';
import { config, getServiceName } from '@/config/env';

interface Retailer {
  id: string;
  name: string;
  display_name: string;
  supported: boolean;
}

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  children?: NavItem[];
}

export const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isRetailersOpen, setIsRetailersOpen] = useState(false);
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [loadingRetailers, setLoadingRetailers] = useState(true);
  const { toggleTheme, resolvedTheme } = useTheme();
  const location = useLocation();

  // Fetch retailers from API
  useEffect(() => {
    const fetchRetailers = async () => {
      try {
        const response = await fetch(`${config.apiUrl}/api/retailers?supported_only=true`);
        const data = await response.json();
        setRetailers(data.retailers || []);
      } catch (error) {
        console.error('Failed to fetch retailers:', error);
        // Fallback to default retailers
        setRetailers([
          { id: 'amazon', name: 'amazon', display_name: 'Amazon', supported: true },
          { id: 'flipkart', name: 'flipkart', display_name: 'Flipkart', supported: true },
          { id: 'croma', name: 'croma', display_name: 'Croma', supported: true }
        ]);
      } finally {
        setLoadingRetailers(false);
      }
    };

    fetchRetailers();
  }, []);

  const navItems: NavItem[] = [
    { label: 'Home', href: '/', icon: Home },
    { label: 'AI Search', href: '#search', icon: Search },
    { label: 'Price Alerts', href: '/alerts', icon: Bell },
    { label: 'Smart Lists', href: '/lists', icon: List },
    { label: 'Analytics', href: '/analytics', icon: BarChart3 },
  ];

  const handleNavClick = (href: string, badge?: string) => {
    if (badge === 'Soon') {
      alert(`${href.split('/').pop()?.replace('-', ' ')} - Coming Soon! We're working hard to bring you this feature.`);
      return false;
    }
    return true;
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 group">
            <motion.div
              whileHover={{ scale: 1.05, rotate: 5 }}
              transition={{ type: "spring", stiffness: 400 }}
              className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"
            >
              {getServiceName()}
            </motion.div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.href || (item.href !== '/' && location.pathname.startsWith(item.href));
              return (
                <Link
                  key={item.label}
                  to={item.href}
                  onClick={(e) => {
                    if (!handleNavClick(item.href, item.badge)) {
                      e.preventDefault();
                    }
                  }}
                  className={`relative px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                    isActive 
                      ? 'text-foreground bg-accent' 
                      : 'text-foreground/80 hover:text-foreground hover:bg-accent/50'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                  {item.badge && (
                    <span className="absolute -top-1 -right-1 px-1.5 py-0.5 text-[10px] font-bold bg-purple-500 text-white rounded-full">
                      {item.badge}
                    </span>
                  )}
                  {isActive && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                      initial={false}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  )}
                </Link>
              );
            })}

            {/* Retailers Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsRetailersOpen(!isRetailersOpen)}
                className="px-3 py-2 rounded-md text-sm font-medium text-foreground/80 hover:text-foreground hover:bg-accent/50 transition-all duration-200 flex items-center gap-2"
                aria-expanded={isRetailersOpen}
                aria-haspopup="true"
              >
                <Store className="w-4 h-4" />
                Retailers
                <ChevronDown className={`w-4 h-4 transition-transform ${isRetailersOpen ? 'rotate-180' : ''}`} />
              </button>

              <AnimatePresence>
                {isRetailersOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute right-0 mt-2 w-56 bg-background border border-border rounded-lg shadow-lg py-2"
                  >
                    {/* Manage Retailers */}
                    <Link
                      to="/retailers/manage"
                      onClick={(e) => {
                        e.preventDefault();
                        alert('Manage Retailers - Coming Soon! You\'ll be able to configure scraping rules and preferences.');
                        setIsRetailersOpen(false);
                      }}
                      className="block px-4 py-2 text-sm text-foreground/80 hover:text-foreground hover:bg-accent/50"
                    >
                      <span className="font-semibold">Manage Retailers</span>
                    </Link>

                    <div className="border-t border-border my-2" />

                    {/* Retailer List */}
                    <div className="px-4 py-2 text-xs text-muted-foreground font-semibold">
                      Supported Retailers
                    </div>
                    {loadingRetailers ? (
                      <div className="px-4 py-2 text-sm text-muted-foreground">Loading...</div>
                    ) : (
                      retailers.map((retailer) => (
                        <Link
                          key={retailer.id}
                          to={`/retailers/${retailer.id}`}
                          onClick={(e) => {
                            e.preventDefault();
                            alert(`${retailer.display_name} - View products from ${retailer.display_name}`);
                            setIsRetailersOpen(false);
                          }}
                          className="block px-4 py-2 text-sm text-foreground/80 hover:text-foreground hover:bg-accent/50"
                        >
                          {retailer.display_name}
                          {retailer.supported && (
                            <span className="ml-2 text-xs text-green-600 dark:text-green-400">✓</span>
                          )}
                        </Link>
                      ))
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              className="ml-2"
              aria-label="Toggle theme"
            >
              {resolvedTheme === 'dark' ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </Button>
          </nav>

          {/* Mobile Menu Button */}
          <div className="flex items-center gap-2 md:hidden">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {resolvedTheme === 'dark' ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              aria-label="Toggle menu"
              aria-expanded={isMenuOpen}
            >
              {isMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        <AnimatePresence>
          {isMenuOpen && (
            <motion.nav
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden border-t border-border py-4"
            >
              {navItems.map((item) => {
                const isActive = location.pathname === item.href || (item.href !== '/' && location.pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.label}
                    to={item.href}
                    onClick={(e) => {
                      if (!handleNavClick(item.href, item.badge)) {
                        e.preventDefault();
                      }
                      setIsMenuOpen(false);
                    }}
                    className={`flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-md relative ${
                      isActive
                        ? 'text-foreground bg-accent'
                        : 'text-foreground/80 hover:text-foreground hover:bg-accent/50'
                    }`}
                  >
                    <item.icon className="w-5 h-5" />
                    {item.label}
                    {item.badge && (
                      <span className="ml-auto px-2 py-1 text-xs font-bold bg-purple-500 text-white rounded-full">
                        {item.badge}
                      </span>
                    )}
                    {isActive && (
                      <span className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r" />
                    )}
                  </Link>
                );
              })}

              {/* Mobile Retailers Section */}
              <div className="mt-4 pt-4 border-t border-border">
                <div className="px-4 py-2 text-xs text-muted-foreground font-semibold flex items-center gap-2">
                  <Store className="w-4 h-4" />
                  Retailers
                </div>
                <Link
                  to="/retailers/manage"
                  onClick={(e) => {
                    e.preventDefault();
                    alert('Manage Retailers - Coming Soon!');
                    setIsMenuOpen(false);
                  }}
                  className="block px-4 py-2 text-sm text-foreground/80 hover:text-foreground hover:bg-accent/50 rounded-md"
                >
                  Manage Retailers
                </Link>
                {retailers.map((retailer) => (
                  <Link
                    key={retailer.id}
                    to={`/retailers/${retailer.id}`}
                    onClick={(e) => {
                      e.preventDefault();
                      alert(`${retailer.display_name} products`);
                      setIsMenuOpen(false);
                    }}
                    className="block px-4 py-2 text-sm text-foreground/80 hover:text-foreground hover:bg-accent/50 rounded-md"
                  >
                    {retailer.display_name}
                    {retailer.supported && (
                      <span className="ml-2 text-xs text-green-600 dark:text-green-400">✓</span>
                    )}
                  </Link>
                ))}
              </div>
            </motion.nav>
          )}
        </AnimatePresence>
      </div>

      {/* Click outside to close dropdowns */}
      {(isRetailersOpen || isMenuOpen) && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setIsRetailersOpen(false);
            setIsMenuOpen(false);
          }}
        />
      )}
    </header>
  );
};
