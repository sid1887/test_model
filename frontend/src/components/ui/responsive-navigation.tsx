
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, ChevronDown } from 'lucide-react';
import { useAccessibility } from '@/hooks/useAccessibility';
import { useTranslation } from '@/i18n';
import { LanguageSwitcher } from './language-switcher';
import { cn } from '@/lib/utils';

interface NavigationItem {
  label: string;
  href: string;
  children?: NavigationItem[];
}

interface ResponsiveNavigationProps {
  items: NavigationItem[];
  logo: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

const ResponsiveNavigation: React.FC<ResponsiveNavigationProps> = ({
  items,
  logo,
  actions,
  className
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const { getAriaProps, getKeyboardProps } = useAccessibility();
  const { t } = useTranslation();

  const toggleMenu = () => setIsOpen(!isOpen);
  const closeMenu = () => setIsOpen(false);

  return (
    <nav className={cn("relative bg-background/95 backdrop-blur-md border-b border-border", className)}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            {logo}
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-8">
              {items.map((item) => (
                <div key={item.label} className="relative group">
                  <button
                    className="text-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 flex items-center gap-1 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                    {...getAriaProps(item.label, !!item.children?.length, `dropdown-${item.label}`)}
                    {...getKeyboardProps(() => {
                      if (item.children) {
                        setActiveDropdown(activeDropdown === item.label ? null : item.label);
                      }
                    })}
                  >
                    {item.label}
                    {item.children && (
                      <ChevronDown className="w-4 h-4 transition-transform duration-200 group-hover:rotate-180" />
                    )}
                  </button>

                  {/* Desktop Dropdown */}
                  {item.children && (
                    <AnimatePresence>
                      {activeDropdown === item.label && (
                        <motion.div
                          initial={{ opacity: 0, y: -10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          transition={{ duration: 0.2 }}
                          className="absolute top-full left-0 mt-2 w-48 bg-popover border border-border rounded-lg shadow-lg py-2 z-50"
                          id={`dropdown-${item.label}`}
                        >
                          {item.children.map((child) => (
                            <a
                              key={child.label}
                              href={child.href}
                              className="block px-4 py-2 text-sm text-popover-foreground hover:bg-accent hover:text-accent-foreground transition-colors duration-150 focus:outline-none focus:bg-accent"
                            >
                              {child.label}
                            </a>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Desktop Actions */}
          <div className="hidden md:flex items-center gap-4">
            <LanguageSwitcher />
            {actions}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={toggleMenu}
              className="inline-flex items-center justify-center p-2 rounded-md text-foreground hover:text-primary hover:bg-accent focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary transition-colors duration-200"
              {...getAriaProps(isOpen ? t('accessibility.menuClose') : t('accessibility.menuOpen'), isOpen, 'mobile-menu')}
            >
              <span className="sr-only">{isOpen ? t('accessibility.menuClose') : t('accessibility.menuOpen')}</span>
              {isOpen ? (
                <X className="block h-6 w-6" aria-hidden="true" />
              ) : (
                <Menu className="block h-6 w-6" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="md:hidden bg-background border-t border-border"
            id="mobile-menu"
          >
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
              {items.map((item) => (
                <div key={item.label}>
                  <a
                    href={item.href}
                    onClick={closeMenu}
                    className="block px-3 py-2 rounded-md text-base font-medium text-foreground hover:text-primary hover:bg-accent transition-colors duration-200 focus:outline-none focus:bg-accent"
                  >
                    {item.label}
                  </a>
                  {item.children && (
                    <div className="pl-4 space-y-1">
                      {item.children.map((child) => (
                        <a
                          key={child.label}
                          href={child.href}
                          onClick={closeMenu}
                          className="block px-3 py-2 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-colors duration-200 focus:outline-none focus:bg-accent"
                        >
                          {child.label}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              <div className="pt-4 pb-3 border-t border-border">
                <div className="flex items-center justify-between px-2">
                  <LanguageSwitcher />
                  {actions}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export { ResponsiveNavigation };
