import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"

export type ToastVariant = 'default' | 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = React.useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast = { ...toast, id };
    setToasts((prev) => [...prev, newToast]);

    // Auto-remove after duration
    const duration = toast.duration || 5000;
    setTimeout(() => {
      removeToast(id);
    }, duration);
  }, [removeToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
};

const ToastContainer: React.FC<{ toasts: Toast[]; removeToast: (id: string) => void }> = ({
  toasts,
  removeToast,
}) => {
  return (
    <div
      className="fixed top-4 right-4 z-[var(--z-toast,999)] flex flex-col gap-2 max-w-md w-full pointer-events-none"
      style={{ zIndex: 'var(--z-toast, 999)' }}
    >
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
        ))}
      </AnimatePresence>
    </div>
  );
};

const ToastItem: React.FC<{ toast: Toast; onClose: () => void }> = ({ toast, onClose }) => {
  const variantConfig = {
    default: {
      icon: Info,
      iconColor: 'text-aether-primary',
      borderColor: 'border-aether-glow/30',
      bgGradient: 'from-aether-primary/10 to-aether-glow/10',
    },
    success: {
      icon: CheckCircle,
      iconColor: 'text-green-500',
      borderColor: 'border-green-500/30',
      bgGradient: 'from-green-500/10 to-emerald-500/10',
    },
    error: {
      icon: AlertCircle,
      iconColor: 'text-red-500',
      borderColor: 'border-red-500/30',
      bgGradient: 'from-red-500/10 to-rose-500/10',
    },
    warning: {
      icon: AlertTriangle,
      iconColor: 'text-yellow-500',
      borderColor: 'border-yellow-500/30',
      bgGradient: 'from-yellow-500/10 to-orange-500/10',
    },
    info: {
      icon: Info,
      iconColor: 'text-blue-500',
      borderColor: 'border-blue-500/30',
      bgGradient: 'from-blue-500/10 to-cyan-500/10',
    },
  };

  const variant = toast.variant || 'default';
  const config = variantConfig[variant];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: 100, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.9 }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 30,
      }}
      className="pointer-events-auto"
    >
      <div
        className={cn(
          "glass-elevated rounded-2xl border shadow-glow p-4",
          "backdrop-blur-xl",
          `bg-gradient-to-r ${config.bgGradient}`,
          config.borderColor
        )}
      >
        <div className="flex items-start gap-3">
          <div className={cn("flex-shrink-0 mt-0.5", config.iconColor)}>
            <Icon className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-foreground mb-1">{toast.title}</h4>
            {toast.description && (
              <p className="text-sm text-muted-foreground">{toast.description}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 rounded-lg p-1 hover:bg-white/10 transition-colors"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default ToastProvider;
