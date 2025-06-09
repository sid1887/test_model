
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAccessibility } from '@/hooks/useAccessibility';
import { cn } from '@/lib/utils';

interface ValidationRule {
  validate: (value: string) => boolean;
  message: string;
}

interface EnhancedInputProps {
  label: string;
  type?: string;
  placeholder?: string;
  required?: boolean;
  validationRules?: ValidationRule[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
  helpText?: string;
}

const EnhancedInput: React.FC<EnhancedInputProps> = ({
  label,
  type = 'text',
  placeholder,
  required,
  validationRules = [],
  value,
  onChange,
  className,
  helpText
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [touched, setTouched] = useState(false);
  const { getAriaProps } = useAccessibility();

  const errors = validationRules
    .filter(rule => !rule.validate(value))
    .map(rule => rule.message);

  const isValid = errors.length === 0 && value.length > 0;
  const hasErrors = errors.length > 0 && touched;
  const inputType = type === 'password' && showPassword ? 'text' : type;

  const inputId = `input-${label.toLowerCase().replace(/\s+/g, '-')}`;
  const errorId = `${inputId}-error`;
  const helpId = `${inputId}-help`;

  return (
    <div className={cn('space-y-2', className)}>
      <Label 
        htmlFor={inputId}
        className={cn(
          'text-sm font-medium transition-colors duration-200',
          hasErrors ? 'text-destructive' : 'text-foreground'
        )}
      >
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>

      <div className="relative">
        <Input
          id={inputId}
          type={inputType}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => {
            setIsFocused(false);
            setTouched(true);
          }}
          className={cn(
            'transition-all duration-200 pr-10',
            isFocused && 'ring-2 ring-primary ring-offset-2',
            hasErrors && 'border-destructive focus:border-destructive',
            isValid && touched && 'border-green-500 focus:border-green-500'
          )}
          aria-describedby={cn(
            helpText && helpId,
            hasErrors && errorId
          )}
          {...getAriaProps(label, undefined, undefined)}
        />

        {/* Password toggle */}
        {type === 'password' && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            {...getAriaProps(showPassword ? 'Hide password' : 'Show password')}
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}

        {/* Validation indicator */}
        {touched && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute right-3 top-1/2 -translate-y-1/2"
          >
            {isValid ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : hasErrors ? (
              <AlertCircle className="w-4 h-4 text-destructive" />
            ) : null}
          </motion.div>
        )}

        {/* Focus ring animation */}
        {isFocused && (
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="absolute inset-0 border-2 border-primary rounded-md pointer-events-none"
          />
        )}
      </div>

      {/* Help text */}
      {helpText && (
        <p id={helpId} className="text-xs text-muted-foreground">
          {helpText}
        </p>
      )}

      {/* Error messages */}
      <AnimatePresence>
        {hasErrors && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            id={errorId}
            className="space-y-1"
          >
            {errors.map((error, index) => (
              <p key={index} className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                {error}
              </p>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

interface FormSectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

const FormSection: React.FC<FormSectionProps> = ({
  title,
  description,
  children,
  className
}) => {
  return (
    <div className={cn('space-y-6', className)}>
      <div>
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
        {description && (
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        )}
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  );
};

export { EnhancedInput, FormSection };
