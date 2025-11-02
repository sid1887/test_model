import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

export interface AetherInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  floatingLabel?: boolean;
  glowOnFocus?: boolean;
}

const AetherInput = React.forwardRef<HTMLInputElement, AetherInputProps>(
  ({ className, type, label, error, floatingLabel = false, glowOnFocus = true, ...props }, ref) => {
    const [isFocused, setIsFocused] = React.useState(false);
    const [hasValue, setHasValue] = React.useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setHasValue(e.target.value.length > 0);
      props.onChange?.(e);
    };

    const inputClasses = cn(
      "flex h-12 w-full rounded-xl border px-4 py-3 text-sm transition-all duration-300",
      "file:border-0 file:bg-transparent file:text-sm file:font-medium",
      "placeholder:text-muted-foreground",
      "focus-visible:outline-none",
      "disabled:cursor-not-allowed disabled:opacity-50",
      glowOnFocus && "focus:shadow-glow focus:border-aether-glow",
      error 
        ? "border-red-500 focus:ring-2 focus:ring-red-500/20" 
        : "border-aether-glow/20 glass-subtle focus:ring-2 focus:ring-aether-glow/20 focus:border-aether-glow",
      floatingLabel && "pt-6 pb-2",
      className
    );

    if (floatingLabel && label) {
      return (
        <div className="relative w-full">
          <input
            type={type}
            className={inputClasses}
            ref={ref}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onChange={handleChange}
            {...props}
          />
          <motion.label
            className={cn(
              "absolute left-4 pointer-events-none transition-all duration-200",
              "text-muted-foreground",
              (isFocused || hasValue)
                ? "top-2 text-xs bg-gradient-to-r from-aether-primary to-aether-glow bg-clip-text text-transparent font-medium"
                : "top-1/2 -translate-y-1/2 text-sm"
            )}
            animate={{
              scale: (isFocused || hasValue) ? 0.9 : 1,
            }}
            transition={{ duration: 0.2 }}
          >
            {label}
          </motion.label>
          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className="text-xs text-red-500 mt-1.5 ml-1"
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      );
    }

    return (
      <div className="relative w-full">
        {label && (
          <label className="block text-sm font-medium mb-2 bg-gradient-to-r from-aether-primary to-aether-glow bg-clip-text text-transparent">
            {label}
          </label>
        )}
        <input
          type={type}
          className={inputClasses}
          ref={ref}
          {...props}
        />
        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className="text-xs text-red-500 mt-1.5 ml-1"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    );
  }
)
AetherInput.displayName = "AetherInput"

export default AetherInput;
