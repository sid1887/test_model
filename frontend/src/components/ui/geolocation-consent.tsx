/**
 * Geolocation Consent Component
 * Handles user location permission with clear consent UI
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, X, Check, AlertCircle } from 'lucide-react';
import { Button } from './button';
import { Card } from './card';
import { config } from '@/config/env';

interface GeolocationConsentProps {
  onLocationGranted?: (location: GeolocationPosition) => void;
  onLocationDenied?: () => void;
}

interface StoredLocation {
  latitude: number;
  longitude: number;
  accuracy?: number;
  city?: string;
  country?: string;
  timestamp: string;
}

export const GeolocationConsent: React.FC<GeolocationConsentProps> = ({
  onLocationGranted,
  onLocationDenied,
}) => {
  const [showPrompt, setShowPrompt] = useState(false);
  const [status, setStatus] = useState<'idle' | 'requesting' | 'granted' | 'denied'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [manualLocation, setManualLocation] = useState({ city: '', country: '' });

  useEffect(() => {
    // Check if user has already made a decision
    const locationConsent = localStorage.getItem('location_consent');
    const storedLocation = localStorage.getItem('user_location');

    if (!locationConsent && !storedLocation) {
      // Show prompt after a short delay for better UX
      const timer = setTimeout(() => {
        setShowPrompt(true);
      }, 2000);
      return () => clearTimeout(timer);
    } else if (locationConsent === 'granted' && storedLocation) {
      setStatus('granted');
    } else if (locationConsent === 'denied') {
      setStatus('denied');
    }
  }, []);

  const requestLocation = async () => {
    setStatus('requesting');
    setError(null);

    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser');
      setStatus('denied');
      return;
    }

    try {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          // Store consent
          localStorage.setItem('location_consent', 'granted');
          
          // Prepare location data
          const locationData: StoredLocation = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: new Date().toISOString(),
          };

          // Store location locally
          localStorage.setItem('user_location', JSON.stringify(locationData));

          // Send to backend
          try {
            await fetch(`${config.apiUrl}/api/user/location`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy,
                consent_given: true,
              }),
            });
          } catch (apiError) {
            console.error('Failed to send location to backend:', apiError);
            // Continue anyway - local storage is enough
          }

          setStatus('granted');
          setShowPrompt(false);
          onLocationGranted?.(position);
        },
        (error) => {
          console.error('Geolocation error:', error);
          setError(error.message);
          setStatus('denied');
          localStorage.setItem('location_consent', 'denied');
          onLocationDenied?.();
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000, // 5 minutes
        }
      );
    } catch (err) {
      setError('Failed to get location');
      setStatus('denied');
      onLocationDenied?.();
    }
  };

  const denyLocation = () => {
    localStorage.setItem('location_consent', 'denied');
    setStatus('denied');
    setShowPrompt(false);
    onLocationDenied?.();
  };

  const handleManualLocation = async () => {
    if (!manualLocation.city || !manualLocation.country) {
      setError('Please enter both city and country');
      return;
    }

    try {
      // Store manual location
      const locationData = {
        city: manualLocation.city,
        country: manualLocation.country,
        timestamp: new Date().toISOString(),
        manual: true,
      };

      localStorage.setItem('user_location', JSON.stringify(locationData));
      localStorage.setItem('location_consent', 'manual');

      // Send to backend
      await fetch(`${config.apiUrl}/api/user/location`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          latitude: 0,
          longitude: 0,
          city: manualLocation.city,
          country: manualLocation.country,
          consent_given: true,
        }),
      });

      setStatus('granted');
      setShowPrompt(false);
    } catch (err) {
      setError('Failed to save location');
    }
  };

  return (
    <>
      <AnimatePresence>
        {showPrompt && status === 'idle' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="w-full max-w-md"
            >
              <Card className="p-6 shadow-2xl">
                <div className="flex items-start gap-4 mb-4">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                    <MapPin className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold mb-2">Find Local Deals Near You</h3>
                    <p className="text-sm text-muted-foreground">
                      We'd like to use your location to show you personalized deals from nearby stores and provide accurate local pricing.
                    </p>
                  </div>
                  <button
                    onClick={denyLocation}
                    className="text-muted-foreground hover:text-foreground"
                    aria-label="Close"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {error && (
                  <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                    <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                  </div>
                )}

                <div className="space-y-3">
                  <Button
                    onClick={requestLocation}
                    disabled={status !== 'idle'}
                    className="w-full"
                  >
                    <Check className="w-4 h-4 mr-2" />
                    {status !== 'idle' ? 'Getting location...' : 'Allow Location Access'}
                  </Button>

                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t border-border" />
                    </div>
                    <div className="relative flex justify-center text-xs">
                      <span className="bg-background px-2 text-muted-foreground">or</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <input
                      type="text"
                      placeholder="Enter your city"
                      value={manualLocation.city}
                      onChange={(e) => setManualLocation({ ...manualLocation, city: e.target.value })}
                      className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                    />
                    <input
                      type="text"
                      placeholder="Enter your country"
                      value={manualLocation.country}
                      onChange={(e) => setManualLocation({ ...manualLocation, country: e.target.value })}
                      className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                    />
                    <Button
                      onClick={handleManualLocation}
                      variant="outline"
                      className="w-full"
                    >
                      Set Location Manually
                    </Button>
                  </div>

                  <Button
                    onClick={denyLocation}
                    variant="ghost"
                    className="w-full text-muted-foreground"
                  >
                    Skip for now
                  </Button>
                </div>

                <p className="mt-4 text-xs text-muted-foreground text-center">
                  Your location data is stored securely and used only to improve your shopping experience. You can change this anytime in settings.
                </p>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Status indicator (optional - shows in corner when granted) */}
      {status === 'granted' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="fixed bottom-4 right-4 z-50 p-3 bg-green-100 dark:bg-green-900/30 rounded-lg shadow-lg flex items-center gap-2"
        >
          <MapPin className="w-4 h-4 text-green-600 dark:text-green-400" />
          <span className="text-sm font-medium text-green-600 dark:text-green-400">
            Location enabled
          </span>
        </motion.div>
      )}
    </>
  );
};
