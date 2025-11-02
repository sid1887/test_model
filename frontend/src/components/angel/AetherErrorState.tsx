import * as React from "react"
import { motion } from "framer-motion"
import { AlertTriangle, RefreshCw, AlertCircle, WifiOff, ServerCrash } from "lucide-react"
import { cn } from "@/lib/utils"
import AetherButton from "./AetherButton"

export type ErrorType = 'generic' | 'network' | 'server' | 'notFound' | 'unauthorized';

interface AetherErrorStateProps {
  type?: ErrorType;
  title?: string;
  message?: string;
  onRetry?: () => void;
  onBack?: () => void;
  className?: string;
}

const errorConfig = {
  generic: {
    icon: AlertCircle,
    defaultTitle: "Something went wrong",
    defaultMessage: "We encountered an unexpected error. Please try again.",
    iconColor: "text-red-500",
    iconBg: "from-red-500/20 to-rose-500/20",
  },
  network: {
    icon: WifiOff,
    defaultTitle: "No internet connection",
    defaultMessage: "Please check your connection and try again.",
    iconColor: "text-orange-500",
    iconBg: "from-orange-500/20 to-amber-500/20",
  },
  server: {
    icon: ServerCrash,
    defaultTitle: "Server error",
    defaultMessage: "Our servers are having issues. Please try again later.",
    iconColor: "text-yellow-500",
    iconBg: "from-yellow-500/20 to-orange-500/20",
  },
  notFound: {
    icon: AlertTriangle,
    defaultTitle: "Page not found",
    defaultMessage: "The page you're looking for doesn't exist.",
    iconColor: "text-blue-500",
    iconBg: "from-blue-500/20 to-cyan-500/20",
  },
  unauthorized: {
    icon: AlertCircle,
    defaultTitle: "Access denied",
    defaultMessage: "You don't have permission to access this resource.",
    iconColor: "text-purple-500",
    iconBg: "from-purple-500/20 to-pink-500/20",
  },
};

const AetherErrorState: React.FC<AetherErrorStateProps> = ({
  type = 'generic',
  title,
  message,
  onRetry,
  onBack,
  className,
}) => {
  const config = errorConfig[type];
  const Icon = config.icon;

  return (
    <div className={cn("flex items-center justify-center min-h-[400px] p-8", className)}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center max-w-md"
      >
        {/* Animated Icon */}
        <motion.div
          className="flex justify-center mb-6"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{
            type: "spring",
            stiffness: 200,
            damping: 15,
            delay: 0.2,
          }}
        >
          <div
            className={cn(
              "relative p-6 rounded-3xl bg-gradient-to-br",
              config.iconBg,
              "shadow-glow"
            )}
          >
            <motion.div
              animate={{
                rotate: [0, 5, -5, 0],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              <Icon className={cn("w-16 h-16", config.iconColor)} />
            </motion.div>
            
            {/* Pulsing ring */}
            <motion.div
              className={cn(
                "absolute inset-0 rounded-3xl border-2",
                config.iconColor.replace('text-', 'border-')
              )}
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 0, 0.5],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />
          </div>
        </motion.div>

        {/* Title */}
        <motion.h2
          className="text-2xl font-bold mb-3 bg-gradient-to-r from-aether-primary to-aether-glow bg-clip-text text-transparent"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          {title || config.defaultTitle}
        </motion.h2>

        {/* Message */}
        <motion.p
          className="text-muted-foreground mb-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          {message || config.defaultMessage}
        </motion.p>

        {/* Action Buttons */}
        <motion.div
          className="flex gap-3 justify-center"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          {onRetry && (
            <AetherButton
              variant="primary"
              onClick={onRetry}
              className="group"
            >
              <RefreshCw className="w-4 h-4 mr-2 group-hover:rotate-180 transition-transform duration-500" />
              Try Again
            </AetherButton>
          )}
          {onBack && (
            <AetherButton
              variant="glass"
              onClick={onBack}
            >
              Go Back
            </AetherButton>
          )}
        </motion.div>
      </motion.div>
    </div>
  );
};

export default AetherErrorState;
