import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  AuroraEnhanced,
  HaloText,
  AetherButton,
  AetherCard,
  AetherInput,
  AetherSkeletonCard,
  AetherErrorState,
  ToastProvider,
  useToast,
  AetherTable,
  AetherTableHeader,
  AetherTableBody,
  AetherTableRow,
  AetherTableHead,
  AetherTableCell,
} from '@/components/angel';
import { useKonamiCode, triggerConfetti, useAchievements, getSeasonalTheme, useClickCounter } from '@/utils/aetherDelight';
import { usePrefersReducedMotion } from '@/utils/aetherMotion';
import { Sparkles, Trophy, Zap, Gift } from 'lucide-react';

const DelightDemo: React.FC = () => {
  const { addToast } = useToast();
  const prefersReducedMotion = usePrefersReducedMotion();
  const { achievements, unlockAchievement, getProgress } = useAchievements();
  const { count: logoClicks, handleClick: handleLogoClick } = useClickCounter(5, () => {
    addToast({
      title: '🎉 Easter Egg Found!',
      description: 'You clicked the logo 5 times!',
      variant: 'success',
      duration: 5000,
    });
    unlockAchievement('konami-master');
  });

  const [showSkeletons, setShowSkeletons] = useState(true);
  const [errorType, setErrorType] = useState<'network' | 'server' | 'generic'>('generic');
  const seasonalTheme = getSeasonalTheme();
  const progress = getProgress();

  // Konami Code Easter Egg
  useKonamiCode(() => {
    triggerConfetti();
    addToast({
      title: '🎮 Konami Code Activated!',
      description: 'Achievement Unlocked: Secret Master',
      variant: 'success',
      duration: 10000,
    });
    unlockAchievement('konami-master');
  });

  useEffect(() => {
    const timer = setTimeout(() => setShowSkeletons(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen relative overflow-x-hidden">
      <AuroraEnhanced />

      <div className="relative z-10 py-12 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <section className="max-w-7xl mx-auto mb-16 text-center">
          <motion.div
            onClick={handleLogoClick}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            className="inline-block cursor-pointer mb-6"
          >
            <Sparkles className="w-16 h-16 text-aether-glow mx-auto" />
          </motion.div>
          <h1 className="aether-hero mb-6">
            <HaloText>Phase 5-7: Polish & Delight</HaloText>
          </h1>
          <p className="aether-subheading max-w-2xl mx-auto">
            Loading states, toasts, error handling, performance optimizations, and delightful surprises
          </p>

          {/* Motion Preference Indicator */}
          {prefersReducedMotion && (
            <div className="mt-4 glass-elevated rounded-xl px-4 py-2 inline-block">
              <p className="text-sm text-muted-foreground">
                ⚡ Reduced Motion Mode Active
              </p>
            </div>
          )}

          {/* Seasonal Theme */}
          {seasonalTheme && (
            <div className="mt-4">
              <AetherCard variant="elevated" className="inline-block px-6 py-3">
                <p className="text-lg">
                  <span className="mr-2">{seasonalTheme.emoji}</span>
                  <span className="bg-gradient-to-r from-aether-primary to-aether-glow bg-clip-text text-transparent font-semibold">
                    {seasonalTheme.name} Theme Active
                  </span>
                </p>
              </AetherCard>
            </div>
          )}
        </section>

        {/* Achievements Section */}
        <section className="max-w-7xl mx-auto mb-16">
          <h2 className="text-3xl font-bold mb-6 text-center bg-gradient-to-r from-aether-primary to-aether-glow bg-clip-text text-transparent">
            <Trophy className="w-8 h-8 inline-block mr-2" />
            Achievements ({progress.unlocked}/{progress.total})
          </h2>
          <div className="mb-4 glass-elevated rounded-full h-3 overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-aether-primary to-aether-glow"
              initial={{ width: 0 }}
              animate={{ width: `${progress.percentage}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {achievements.map((achievement) => (
              <AetherCard
                key={achievement.id}
                variant={achievement.unlocked ? 'elevated' : 'subtle'}
                className={achievement.unlocked ? 'border-aether-glow/50' : 'opacity-60'}
              >
                <div className="flex items-start gap-3">
                  <span className="text-3xl">{achievement.icon}</span>
                  <div className="flex-1">
                    <h4 className="font-semibold mb-1">{achievement.title}</h4>
                    <p className="text-sm text-muted-foreground mb-2">{achievement.description}</p>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      achievement.rarity === 'legendary' ? 'bg-gradient-to-r from-yellow-500/20 to-orange-500/20 text-yellow-500' :
                      achievement.rarity === 'epic' ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-purple-500' :
                      achievement.rarity === 'rare' ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-blue-500' :
                      'bg-muted text-muted-foreground'
                    }`}>
                      {achievement.rarity}
                    </span>
                  </div>
                </div>
              </AetherCard>
            ))}
          </div>
        </section>

        {/* Toast Notifications */}
        <section className="max-w-7xl mx-auto mb-16">
          <h2 className="text-3xl font-bold mb-6 text-center">Toast Notifications</h2>
          <div className="flex flex-wrap gap-3 justify-center">
            <AetherButton
              variant="primary"
              onClick={() => addToast({ title: 'Success!', description: 'Operation completed', variant: 'success' })}
            >
              Success Toast
            </AetherButton>
            <AetherButton
              variant="accent"
              onClick={() => addToast({ title: 'Error', description: 'Something went wrong', variant: 'error' })}
            >
              Error Toast
            </AetherButton>
            <AetherButton
              variant="glass"
              onClick={() => addToast({ title: 'Warning', description: 'Please check your input', variant: 'warning' })}
            >
              Warning Toast
            </AetherButton>
            <AetherButton
              variant="secondary"
              onClick={() => addToast({ title: 'Info', description: 'Here is some information', variant: 'info' })}
            >
              Info Toast
            </AetherButton>
            <AetherButton
              variant="ghost"
              onClick={triggerConfetti}
            >
              <Gift className="w-4 h-4 mr-2" />
              Trigger Confetti
            </AetherButton>
          </div>
        </section>

        {/* Loading Skeletons */}
        <section className="max-w-7xl mx-auto mb-16">
          <h2 className="text-3xl font-bold mb-6 text-center">Loading Skeletons</h2>
          <div className="flex justify-center mb-4">
            <AetherButton onClick={() => setShowSkeletons(!showSkeletons)}>
              {showSkeletons ? 'Show Content' : 'Show Skeletons'}
            </AetherButton>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {showSkeletons ? (
              <>
                <AetherSkeletonCard />
                <AetherSkeletonCard />
                <AetherSkeletonCard />
              </>
            ) : (
              <>
                {[1, 2, 3].map((i) => (
                  <AetherCard key={i} variant="elevated">
                    <img
                      src={`https://picsum.photos/400/300?random=${i}`}
                      alt={`Product ${i}`}
                      className="w-full h-48 object-cover rounded-xl mb-4"
                    />
                    <h3 className="font-semibold mb-2">Product {i}</h3>
                    <p className="text-muted-foreground text-sm">Amazing product description here</p>
                  </AetherCard>
                ))}
              </>
            )}
          </div>
        </section>

        {/* Error States */}
        <section className="max-w-7xl mx-auto mb-16">
          <h2 className="text-3xl font-bold mb-6 text-center">Error States</h2>
          <div className="flex gap-3 justify-center mb-6">
            <AetherButton size="sm" onClick={() => setErrorType('generic')}>Generic</AetherButton>
            <AetherButton size="sm" onClick={() => setErrorType('network')}>Network</AetherButton>
            <AetherButton size="sm" onClick={() => setErrorType('server')}>Server</AetherButton>
          </div>
          <AetherCard variant="elevated">
            <AetherErrorState
              type={errorType}
              onRetry={() => addToast({ title: 'Retrying...', variant: 'info' })}
              onBack={() => addToast({ title: 'Going back...', variant: 'info' })}
            />
          </AetherCard>
        </section>

        {/* Enhanced Input */}
        <section className="max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold mb-6 text-center">Enhanced Inputs</h2>
          <div className="space-y-4">
            <AetherInput label="Standard Input" placeholder="Enter text..." />
            <AetherInput label="Floating Label" floatingLabel placeholder="Start typing..." />
            <AetherInput label="With Error" error="This field is required" placeholder="Enter text..." />
            <AetherInput label="No Glow" glowOnFocus={false} placeholder="No glow effect..." />
          </div>
        </section>

        {/* Enhanced Table */}
        <section className="max-w-7xl mx-auto mb-16">
          <h2 className="text-3xl font-bold mb-6 text-center">Enhanced Tables</h2>
          <AetherCard variant="elevated">
            <AetherTable>
              <AetherTableHeader>
                <AetherTableRow>
                  <AetherTableHead>Product</AetherTableHead>
                  <AetherTableHead>Price</AetherTableHead>
                  <AetherTableHead>Status</AetherTableHead>
                  <AetherTableHead>Actions</AetherTableHead>
                </AetherTableRow>
              </AetherTableHeader>
              <AetherTableBody>
                {[1, 2, 3, 4, 5].map((i) => (
                  <AetherTableRow key={i}>
                    <AetherTableCell>Product {i}</AetherTableCell>
                    <AetherTableCell>${(Math.random() * 100).toFixed(2)}</AetherTableCell>
                    <AetherTableCell>
                      <span className="px-2 py-1 rounded-full text-xs bg-green-500/20 text-green-500">
                        In Stock
                      </span>
                    </AetherTableCell>
                    <AetherTableCell>
                      <AetherButton size="sm" variant="ghost">View</AetherButton>
                    </AetherTableCell>
                  </AetherTableRow>
                ))}
              </AetherTableBody>
            </AetherTable>
          </AetherCard>
        </section>

        {/* Easter Egg Hint */}
        <section className="max-w-xl mx-auto text-center">
          <AetherCard variant="glass" className="p-8">
            <Zap className="w-12 h-12 text-aether-glow mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-3">
              <HaloText>Hidden Secrets</HaloText>
            </h3>
            <p className="text-muted-foreground mb-4">
              Try the classic Konami Code (↑ ↑ ↓ ↓ ← → ← → B A) or click the sparkle logo 5 times!
            </p>
            <p className="text-xs text-muted-foreground">
              Logo clicks: {logoClicks}/5
            </p>
          </AetherCard>
        </section>
      </div>
    </div>
  );
};

const DelightDemoWithToast = () => (
  <ToastProvider>
    <DelightDemo />
  </ToastProvider>
);

export default DelightDemoWithToast;
