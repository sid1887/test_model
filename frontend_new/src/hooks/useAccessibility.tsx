
import { useEffect, useRef, useState } from 'react';

interface UseAccessibilityOptions {
  announceChange?: boolean;
  focusOnMount?: boolean;
  trapFocus?: boolean;
}

export const useAccessibility = (options: UseAccessibilityOptions = {}) => {
  const { announceChange = false, focusOnMount = false, trapFocus = false } = options;
  const ref = useRef<HTMLElement>(null);
  const [announcement, setAnnouncement] = useState<string>('');

  // Focus management
  useEffect(() => {
    if (focusOnMount && ref.current) {
      ref.current.focus();
    }
  }, [focusOnMount]);

  // Screen reader announcements
  const announce = (message: string) => {
    setAnnouncement(message);
    setTimeout(() => setAnnouncement(''), 100);
  };

  // Focus trap for modals/dialogs
  useEffect(() => {
    if (!trapFocus || !ref.current) return;

    const element = ref.current;
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      }
      if (e.key === 'Escape') {
        element.focus();
      }
    };

    element.addEventListener('keydown', handleKeyDown);
    return () => element.removeEventListener('keydown', handleKeyDown);
  }, [trapFocus]);

  return {
    ref,
    announce,
    announcement,
    // ARIA helpers
    getAriaProps: (label: string, expanded?: boolean, controls?: string) => ({
      'aria-label': label,
      'aria-expanded': expanded,
      'aria-controls': controls,
      'role': 'button',
      'tabIndex': 0,
    }),
    // Keyboard navigation helper
    getKeyboardProps: (onEnter: () => void, onSpace: () => void = onEnter) => ({
      onKeyDown: (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') onEnter();
        if (e.key === ' ') {
          e.preventDefault();
          onSpace();
        }
      },
    }),
  };
};

// Screen reader announcement component
export const ScreenReaderAnnouncement: React.FC<{ message: string }> = ({ message }) => (
  <div
    aria-live="polite"
    aria-atomic="true"
    className="sr-only"
  >
    {message}
  </div>
);
