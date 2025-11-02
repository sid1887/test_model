import { motion } from 'framer-motion';
import { 
  AuroraEnhanced, 
  HaloText, 
  AetherButton, 
  AetherCard,
  ServiceOrb
} from '@/components/angel';
import { Sparkles, Zap, TrendingUp, Shield } from 'lucide-react';

/**
 * Aether Design System Showcase
 * Live demonstration of all Aether components and design tokens
 */
export default function AetherShowcase() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      {/* Enhanced Aurora Background */}
      <AuroraEnhanced />

      {/* Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        {/* Hero Section */}
        <section className="text-center mb-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="aether-hero mb-6">
              <HaloText>Aether Design System</HaloText>
            </h1>
            <p className="aether-subheading max-w-3xl mx-auto mb-8">
              A cosmic design language that transcends ordinary interfaces with ethereal gradients, 
              fluid animations, and glass-morphic depth.
            </p>
            
            {/* Button Showcase */}
            <div className="flex flex-wrap gap-4 justify-center items-center">
              <AetherButton variant="primary" glow>
                Primary with Glow
              </AetherButton>
              <AetherButton variant="accent">
                Accent Button
              </AetherButton>
              <AetherButton variant="glass">
                Glass Button
              </AetherButton>
              <AetherButton variant="secondary" size="sm">
                Secondary Small
              </AetherButton>
              <AetherButton variant="ghost" size="lg">
                Ghost Large
              </AetherButton>
              <AetherButton variant="primary" isLoading loadingText="Processing...">
                Loading State
              </AetherButton>
            </div>
          </motion.div>
        </section>

        {/* Color Palette */}
        <section className="mb-32">
          <h2 className="text-3xl font-bold mb-12 text-center">
            <span className="aether-accent-text">Color Pantheon</span>
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { name: 'Primary', class: 'bg-aether-primary' },
              { name: 'Glow', class: 'bg-aether-glow' },
              { name: 'Accent', class: 'bg-aether-accent' },
              { name: 'Foreground', class: 'bg-aether-foreground' },
            ].map((color) => (
              <motion.div
                key={color.name}
                whileHover={{ scale: 1.05 }}
                className="glass-elevated p-6 rounded-2xl text-center"
              >
                <div className={`${color.class} h-24 rounded-xl mb-4 shadow-glow`} />
                <p className="font-semibold">{color.name}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Card Variants */}
        <section className="mb-32">
          <h2 className="text-3xl font-bold mb-12 text-center">
            <span className="aether-accent-text">Card Components</span>
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <AetherCard variant="elevated" glow tilt>
              <div className="flex items-start gap-4">
                <div className="p-3 bg-gradient-to-br from-aether-primary to-aether-glow rounded-xl">
                  <Sparkles className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Elevated Card</h3>
                  <p className="text-muted-foreground text-sm">
                    Glass elevated variant with 3D tilt and glow border on hover
                  </p>
                </div>
              </div>
            </AetherCard>

            <AetherCard variant="glass" hover>
              <div className="flex items-start gap-4">
                <div className="p-3 bg-gradient-to-br from-aether-accent to-aether-primary rounded-xl">
                  <Zap className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Glass Card</h3>
                  <p className="text-muted-foreground text-sm">
                    Pure glass morphism with backdrop blur
                  </p>
                </div>
              </div>
            </AetherCard>

            <AetherCard variant="solid" tilt>
              <div className="flex items-start gap-4">
                <div className="p-3 bg-gradient-to-br from-aether-glow to-aether-primary rounded-xl">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg mb-2">Solid Card</h3>
                  <p className="text-muted-foreground text-sm">
                    Traditional card with tilt interaction
                  </p>
                </div>
              </div>
            </AetherCard>
          </div>
        </section>

        {/* Typography Scale */}
        <section className="mb-32">
          <h2 className="text-3xl font-bold mb-12 text-center">
            <span className="aether-accent-text">Typography Hierarchy</span>
          </h2>
          
          <AetherCard variant="elevated" className="space-y-6">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Hero (aether-hero)</p>
              <h1 className="aether-hero">Cosmic Headlines</h1>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-2">Subheading (aether-subheading)</p>
              <p className="aether-subheading">Supporting narrative text</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-2">Accent Text</p>
              <p className="aether-accent-text text-2xl font-semibold">Highlighted content</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-2">Body Text</p>
              <p className="text-base leading-relaxed text-foreground/90">
                Standard paragraph text with optimal readability and comfortable line-height 
                for extended reading experiences.
              </p>
            </div>
          </AetherCard>
        </section>

        {/* Shadows & Effects */}
        <section className="mb-32">
          <h2 className="text-3xl font-bold mb-12 text-center">
            <span className="aether-accent-text">Shadows with Soul</span>
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { name: 'Aether Shadow', class: 'shadow-aether' },
              { name: 'Float Shadow', class: 'shadow-float' },
              { name: 'Glow Effect', class: 'shadow-glow' },
            ].map((shadow) => (
              <motion.div
                key={shadow.name}
                whileHover={{ y: -4 }}
                className={`glass-elevated p-8 rounded-2xl text-center ${shadow.class}`}
              >
                <div className="inline-block p-4 bg-gradient-aether-hero rounded-full mb-4">
                  <TrendingUp className="h-8 w-8 text-white" />
                </div>
                <p className="font-semibold">{shadow.name}</p>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Gradients */}
        <section className="mb-32">
          <h2 className="text-3xl font-bold mb-12 text-center">
            <span className="aether-accent-text">Gradients as Gods</span>
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="h-48 rounded-2xl bg-gradient-aether-hero flex items-center justify-center text-white font-semibold text-xl shadow-aether"
            >
              Aether Hero Gradient
            </motion.div>
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="h-48 rounded-2xl bg-gradient-cosmic flex items-center justify-center text-white font-semibold text-xl shadow-float"
            >
              Cosmic Gradient
            </motion.div>
          </div>
        </section>

        {/* Service Status */}
        <section className="mb-32">
          <h2 className="text-3xl font-bold mb-12 text-center">
            <span className="aether-accent-text">Interactive Elements</span>
          </h2>
          
          <AetherCard variant="glass" className="flex items-center justify-around py-12">
            <div className="text-center">
              <ServiceOrb />
              <p className="mt-4 text-sm font-medium">Service Health</p>
            </div>
            <div className="text-center space-y-2">
              <motion.div
                className="w-16 h-16 rounded-full bg-gradient-border-orb mx-auto"
                animate={{ rotate: 360 }}
                transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
              />
              <p className="text-sm font-medium">Rotating Orb</p>
            </div>
            <div className="text-center space-y-2">
              <motion.div
                className="w-16 h-16 rounded-full bg-aether-accent mx-auto"
                animate={{ scale: [1, 1.2, 1], opacity: [1, 0.6, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              <p className="text-sm font-medium">Pulse Animation</p>
            </div>
          </AetherCard>
        </section>

        {/* Animations */}
        <section className="mb-32">
          <h2 className="text-3xl font-bold mb-12 text-center">
            <span className="aether-accent-text">Motion Catalog</span>
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: 'Float', class: 'animate-float' },
              { name: 'Rotate', class: 'animate-rotate-slow' },
              { name: 'Pulse Scale', class: 'animate-pulse-scale' },
              { name: 'Shimmer', class: 'animate-aether-shimmer' },
            ].map((anim) => (
              <div key={anim.name} className="glass-elevated p-6 rounded-xl text-center">
                <div className={`w-12 h-12 mx-auto mb-3 bg-gradient-to-br from-aether-primary to-aether-glow rounded-lg ${anim.class}`} />
                <p className="text-sm font-medium">{anim.name}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
