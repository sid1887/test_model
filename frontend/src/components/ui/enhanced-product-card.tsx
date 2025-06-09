
import React, { useState } from 'react';
import { motion, useTransform, useMotionValue } from 'framer-motion';
import { Heart, Star, ShoppingCart, ExternalLink, Eye } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface EnhancedProductCardProps {
  id: string;
  name: string;
  price: string;
  originalPrice?: string;
  rating: number;
  reviewCount: number;
  image: string;
  store: string;
  discount?: string;
  isLiked?: boolean;
  onLike?: (id: string) => void;
  onAddToCart?: (id: string) => void;
  className?: string;
}

const EnhancedProductCard: React.FC<EnhancedProductCardProps> = ({
  id,
  name,
  price,
  originalPrice,
  rating,
  reviewCount,
  image,
  store,
  discount,
  isLiked = false,
  onLike,
  onAddToCart,
  className
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  
  const rotateX = useTransform(mouseY, [-150, 150], [15, -15]);
  const rotateY = useTransform(mouseX, [-150, 150], [-15, 15]);

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    mouseX.set(e.clientX - centerX);
    mouseY.set(e.clientY - centerY);
  };

  return (
    <motion.div
      className={cn("group relative perspective-1000", className)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onMouseMove={handleMouseMove}
      style={{ perspective: 1000 }}
    >
      <motion.div
        style={{
          rotateX,
          rotateY,
          transformStyle: "preserve-3d",
        }}
        animate={{
          z: isHovered ? 50 : 0,
        }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="relative"
      >
        <Card className="overflow-hidden backdrop-blur-md bg-white/90 dark:bg-black/80 border border-white/20 dark:border-white/10 shadow-2xl transition-all duration-500 group-hover:shadow-purple-500/25">
          {/* Image Container with Enhanced Effects */}
          <div className="relative overflow-hidden aspect-square">
            <motion.img
              src={image || "/placeholder.svg"}
              alt={name}
              className="w-full h-full object-cover"
              animate={{
                scale: isHovered ? 1.1 : 1,
                filter: isHovered ? "brightness(1.1)" : "brightness(1)",
              }}
              transition={{ duration: 0.6 }}
            />
            
            {/* Animated Gradient Overlay */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"
              animate={{
                opacity: isHovered ? 1 : 0,
              }}
              transition={{ duration: 0.3 }}
            />

            {/* Discount Badge with Pulse */}
            {discount && (
              <motion.div
                initial={{ scale: 0, rotate: -45 }}
                animate={{ scale: 1, rotate: 0 }}
                whileHover={{ scale: 1.1 }}
                className="absolute top-3 left-3 bg-gradient-to-r from-red-500 to-pink-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg"
              >
                <motion.span
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  {discount}
                </motion.span>
              </motion.div>
            )}

            {/* Enhanced Action Buttons */}
            <motion.div
              className="absolute top-3 right-3 flex flex-col gap-2"
              animate={{
                y: isHovered ? 0 : -20,
                opacity: isHovered ? 1 : 0.7,
              }}
            >
              <motion.button
                whileHover={{ scale: 1.2, rotate: 10 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => onLike?.(id)}
                className={cn(
                  "p-2 rounded-full backdrop-blur-md transition-all duration-300 shadow-lg",
                  isLiked 
                    ? "bg-red-500 text-white" 
                    : "bg-white/80 text-gray-600 hover:bg-white hover:text-red-500"
                )}
              >
                <Heart className={cn("w-4 h-4", isLiked && "fill-current")} />
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.2, rotate: -10 }}
                whileTap={{ scale: 0.9 }}
                className="p-2 rounded-full backdrop-blur-md bg-white/80 text-gray-600 hover:bg-white hover:text-blue-500 transition-all duration-300 shadow-lg"
              >
                <Eye className="w-4 h-4" />
              </motion.button>
            </motion.div>

            {/* Interactive Hover Overlay */}
            <motion.div
              className="absolute inset-0 flex items-center justify-center"
              animate={{
                opacity: isHovered ? 1 : 0,
                backdropFilter: isHovered ? "blur(2px)" : "blur(0px)",
              }}
              transition={{ duration: 0.3 }}
            >
              <div className="flex gap-4">
                <motion.button
                  initial={{ scale: 0, y: 50 }}
                  animate={{ 
                    scale: isHovered ? 1 : 0, 
                    y: isHovered ? 0 : 50 
                  }}
                  transition={{ delay: 0.1 }}
                  whileHover={{ scale: 1.1, y: -5 }}
                  onClick={() => onAddToCart?.(id)}
                  className="p-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full shadow-2xl hover:shadow-blue-500/50 transition-all duration-300"
                >
                  <ShoppingCart className="w-5 h-5" />
                </motion.button>
                
                <motion.button
                  initial={{ scale: 0, y: 50 }}
                  animate={{ 
                    scale: isHovered ? 1 : 0, 
                    y: isHovered ? 0 : 50 
                  }}
                  transition={{ delay: 0.2 }}
                  whileHover={{ scale: 1.1, y: -5 }}
                  className="p-4 bg-gradient-to-r from-green-500 to-blue-600 text-white rounded-full shadow-2xl hover:shadow-green-500/50 transition-all duration-300"
                >
                  <ExternalLink className="w-5 h-5" />
                </motion.button>
              </div>
            </motion.div>
          </div>

          {/* Enhanced Content Section */}
          <motion.div 
            className="p-6 space-y-4"
            animate={{
              y: isHovered ? -5 : 0,
            }}
            transition={{ duration: 0.3 }}
          >
            {/* Store and Rating Row */}
            <div className="flex items-center justify-between">
              <motion.span 
                className="px-3 py-1 bg-gradient-to-r from-blue-500/10 to-purple-500/10 text-blue-600 dark:text-blue-400 text-xs font-medium rounded-full border border-blue-500/20"
                whileHover={{ scale: 1.05 }}
              >
                {store}
              </motion.span>
              
              <motion.div 
                className="flex items-center gap-1"
                whileHover={{ scale: 1.05 }}
              >
                <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                <span className="text-sm font-medium">{rating}</span>
                <span className="text-xs text-muted-foreground">({reviewCount})</span>
              </motion.div>
            </div>

            {/* Product Name with Gradient Hover */}
            <motion.h3 
              className="font-semibold text-lg leading-tight line-clamp-2 transition-all duration-300"
              whileHover={{
                background: "linear-gradient(45deg, #3b82f6, #8b5cf6)",
                backgroundClip: "text",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              {name}
            </motion.h3>

            {/* Enhanced Price Section */}
            <div className="flex items-center gap-3">
              <motion.span 
                className="text-2xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent"
                whileHover={{ scale: 1.05 }}
              >
                {price}
              </motion.span>
              {originalPrice && (
                <motion.span 
                  className="text-sm text-muted-foreground line-through"
                  initial={{ opacity: 0.7 }}
                  whileHover={{ opacity: 1 }}
                >
                  {originalPrice}
                </motion.span>
              )}
            </div>
          </motion.div>
        </Card>
      </motion.div>
    </motion.div>
  );
};

export { EnhancedProductCard };
