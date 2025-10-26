
import React from 'react';
import { motion } from 'framer-motion';
import { Heart, Star, ShoppingCart, ExternalLink, TrendingDown, MapPin } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';

// Seed data compatible interface
interface SeedProductCardProps {
  id: string;
  title: string;
  price: number;
  oldPrice?: number | null;
  currency: string;
  store: string;
  store_key: string;
  image_url: string;
  rating: number;
  rating_count: number;
  categories?: string[];
  location?: string;
  availability?: string;
  description?: string;
  url: string;
  onCompare?: (id: string, selected: boolean) => void;
  onWishlist?: (id: string) => void;
  isSelected?: boolean;
  isWishlisted?: boolean;
  className?: string;
}

// Legacy interface for backward compatibility
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

const formatPrice = (price: number, currency: string): string => {
  const currencySymbol = currency === 'USD' ? '$' : '₹';
  return `${currencySymbol}${price.toLocaleString()}`;
};

const calculateDiscount = (price: number, oldPrice: number | null): number | null => {
  if (!oldPrice || oldPrice <= price) return null;
  return Math.round(((oldPrice - price) / oldPrice) * 100);
};

// Seed-compatible component
const SeedProductCard: React.FC<SeedProductCardProps> = ({
  id,
  title,
  price,
  oldPrice,
  currency,
  store,
  image_url,
  rating,
  rating_count,
  categories = [],
  location,
  availability = 'In Stock',
  description,
  url,
  onCompare,
  onWishlist,
  isSelected = false,
  isWishlisted = false,
  className
}) => {
  const discount = calculateDiscount(price, oldPrice ?? null);
  const isInStock = availability.toLowerCase().includes('in stock');

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -8 }}
      transition={{ duration: 0.2 }}
      className={cn("h-full", className)}
    >
      <Card className="relative h-full flex flex-col overflow-hidden bg-card/50 backdrop-blur-sm border-border/50 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 transition-all duration-300">
        {/* Compare Checkbox - Top Right */}
        {onCompare && (
          <div className="absolute top-3 right-3 z-10 bg-background/90 backdrop-blur-sm rounded-md p-1.5 shadow-md">
            <Checkbox
              checked={isSelected}
              onCheckedChange={(checked) => onCompare(id, checked as boolean)}
              aria-label={`Compare ${title}`}
              className="h-5 w-5"
            />
          </div>
        )}

        {/* Discount Badge - Top Left */}
        {discount && (
          <div className="absolute top-3 left-3 z-10">
            <Badge variant="destructive" className="flex items-center gap-1 font-bold shadow-lg">
              <TrendingDown className="h-3 w-3" />
              {discount}% OFF
            </Badge>
          </div>
        )}

        {/* Product Image */}
        <div className="relative w-full aspect-square bg-muted/30 overflow-hidden">
          <img
            src={image_url}
            alt={title}
            className="w-full h-full object-contain p-4 transition-transform duration-300 hover:scale-105"
            loading="lazy"
            onError={(e) => {
              e.currentTarget.src = '/placeholder.svg';
            }}
          />
          
          {!isInStock && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center">
              <Badge variant="secondary">Out of Stock</Badge>
            </div>
          )}
        </div>

        <div className="flex-1 flex flex-col p-4 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <Badge variant="outline" className="text-xs">{store}</Badge>
            {location && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <MapPin className="h-3 w-3" />
                {location}
              </div>
            )}
          </div>

          <h3 className="font-semibold text-base leading-tight line-clamp-2 min-h-[2.5rem]" title={title}>
            {title}
          </h3>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
              <span className="font-semibold text-sm">{rating.toFixed(1)}</span>
            </div>
            <span className="text-xs text-muted-foreground">
              ({rating_count.toLocaleString()})
            </span>
          </div>

          {description && (
            <p className="text-xs text-muted-foreground line-clamp-2">{description}</p>
          )}

          <div className="flex items-baseline gap-2 mt-auto pt-2">
            <span className="text-2xl font-bold text-primary">{formatPrice(price, currency)}</span>
            {oldPrice && (
              <span className="text-sm text-muted-foreground line-through">
                {formatPrice(oldPrice, currency)}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 pt-2">
            <Button
              asChild
              className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg"
              disabled={!isInStock}
            >
              <a href={url} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2">
                <ShoppingCart className="h-4 w-4" />
                {isInStock ? 'View Deal' : 'Unavailable'}
              </a>
            </Button>

            {onWishlist && (
              <Button
                variant={isWishlisted ? "default" : "outline"}
                size="icon"
                onClick={() => onWishlist(id)}
                aria-label={isWishlisted ? `Remove from wishlist` : `Add to wishlist`}
                className={isWishlisted ? "bg-red-500 hover:bg-red-600" : ""}
              >
                <Heart className={`h-4 w-4 ${isWishlisted ? 'fill-current' : ''}`} />
              </Button>
            )}
          </div>

          {categories.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-2 border-t border-border/50">
              {categories.slice(0, 3).map((cat, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">{cat}</Badge>
              ))}
              {categories.length > 3 && (
                <Badge variant="secondary" className="text-xs">+{categories.length - 3}</Badge>
              )}
            </div>
          )}
        </div>
      </Card>
    </motion.div>
  );
};

// Legacy component for backward compatibility
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
        <div className="relative overflow-hidden aspect-square">
          <motion.img
            src={image || "/placeholder.svg"}
            alt={name}
            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
            whileHover={{ scale: 1.1 }}
          />
          
          {discount && (
            <motion.div
              initial={{ scale: 0, rotate: -45 }}
              animate={{ scale: 1, rotate: 0 }}
              className="absolute top-3 left-3 bg-gradient-to-r from-red-500 to-pink-500 text-white px-2 py-1 rounded-full text-xs font-bold shadow-lg"
            >
              {discount}
            </motion.div>
          )}

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

        <div className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="px-2 py-1 bg-gradient-to-r from-blue-500/10 to-purple-500/10 text-blue-600 dark:text-blue-400 text-xs font-medium rounded-full border border-blue-500/20">
              {store}
            </span>
            
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <span className="text-sm font-medium">{rating}</span>
              <span className="text-xs text-muted-foreground">({reviewCount})</span>
            </div>
          </div>

          <h3 className="font-semibold text-lg leading-tight line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-300">
            {name}
          </h3>

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

export { ProductCard, SeedProductCard };
