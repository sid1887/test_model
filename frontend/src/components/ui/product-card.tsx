
import React from 'react';
import { motion } from 'framer-motion';
import { Heart, Star, ShoppingCart, ExternalLink } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface ProductCardProps {
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

const ProductCard: React.FC<ProductCardProps> = ({
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
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -8, rotateY: 5 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className={cn("group relative", className)}
    >
      <Card className="overflow-hidden backdrop-blur-sm bg-white/90 dark:bg-black/80 border border-white/20 dark:border-white/10 shadow-xl hover:shadow-2xl transition-all duration-500">
        {/* Image Container */}
        <div className="relative overflow-hidden aspect-square">
          <motion.img
            src={image || "/placeholder.svg"}
            alt={name}
            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
            whileHover={{ scale: 1.1 }}
          />
          
          {/* Discount Badge */}
          {discount && (
            <motion.div
              initial={{ scale: 0, rotate: -45 }}
              animate={{ scale: 1, rotate: 0 }}
              className="absolute top-3 left-3 bg-gradient-to-r from-red-500 to-pink-500 text-white px-2 py-1 rounded-full text-xs font-bold shadow-lg"
            >
              {discount}
            </motion.div>
          )}

          {/* Like Button */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => onLike?.(id)}
            className={cn(
              "absolute top-3 right-3 p-2 rounded-full backdrop-blur-md transition-all duration-300",
              isLiked 
                ? "bg-red-500 text-white shadow-lg" 
                : "bg-white/80 text-gray-600 hover:bg-white hover:text-red-500"
            )}
          >
            <Heart className={cn("w-4 h-4", isLiked && "fill-current")} />
          </motion.button>

          {/* Hover Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            whileHover={{ opacity: 1 }}
            className="absolute inset-0 bg-black/20 backdrop-blur-[1px] flex items-center justify-center"
          >
            <div className="flex gap-2">
              <motion.button
                initial={{ scale: 0 }}
                whileHover={{ scale: 1.1 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.1 }}
                onClick={() => onAddToCart?.(id)}
                className="p-3 bg-white/90 text-gray-800 rounded-full shadow-xl hover:bg-white transition-all duration-300"
              >
                <ShoppingCart className="w-5 h-5" />
              </motion.button>
              
              <motion.button
                initial={{ scale: 0 }}
                whileHover={{ scale: 1.1 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2 }}
                className="p-3 bg-white/90 text-gray-800 rounded-full shadow-xl hover:bg-white transition-all duration-300"
              >
                <ExternalLink className="w-5 h-5" />
              </motion.button>
            </div>
          </motion.div>
        </div>

        {/* Content */}
        <div className="p-4 space-y-3">
          {/* Store Badge */}
          <div className="flex items-center justify-between">
            <span className="px-2 py-1 bg-gradient-to-r from-blue-500/10 to-purple-500/10 text-blue-600 dark:text-blue-400 text-xs font-medium rounded-full border border-blue-500/20">
              {store}
            </span>
            
            {/* Rating */}
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <span className="text-sm font-medium">{rating}</span>
              <span className="text-xs text-muted-foreground">({reviewCount})</span>
            </div>
          </div>

          {/* Product Name */}
          <h3 className="font-semibold text-lg leading-tight line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-300">
            {name}
          </h3>

          {/* Price */}
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              {price}
            </span>
            {originalPrice && (
              <span className="text-sm text-muted-foreground line-through">
                {originalPrice}
              </span>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export { ProductCard };
