import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, Star, ShoppingCart, Eye, Plus, ChevronDown, ChevronUp, Info } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface ValueScoredProductCardProps {
  id: string;
  name: string;
  price: string;
  originalPrice?: string;
  valueScore: number;
  rating: number;
  reviewCount: number;
  image: string;
  store: string;
  discount?: string;
  specs: string[];
  isLiked?: boolean;
  isComparing?: boolean;
  onLike?: (id: string) => void;
  onAddToCart?: (id: string) => void;
  onCompare?: (id: string) => void;
  className?: string;
  isLoading?: boolean;
}

type ScoreColor = "text-green-500" | "text-yellow-500" | "text-orange-500" | "text-red-500";

const getScoreColor = (score: number): ScoreColor => {
  if (score >= 4) return "text-green-500";
  if (score >= 3) return "text-yellow-500";
  if (score >= 2) return "text-orange-500";
  return "text-red-500";
};

const ValueScoredProductCard: React.FC<ValueScoredProductCardProps> = ({
  id,
  name,
  price,
  originalPrice,
  valueScore,
  rating,
  reviewCount,
  image,
  store,
  discount,
  specs,
  isLiked = false,
  isComparing = false,
  onLike,
  onAddToCart,
  onCompare,
  className,
  isLoading = false
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [showAllSpecs, setShowAllSpecs] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);

  const handleLikeClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onLike?.(id);
  };

  const handleAddToCartClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onAddToCart?.(id);
  };

  const handleCompareClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onCompare?.(id);
  };

  if (isLoading) {
    return (
      <Card className={cn("overflow-hidden", className)}>
        <div className="aspect-square p-4">
          <Skeleton className="w-full h-full rounded-lg" />
        </div>
        <div className="p-4 space-y-3">
          <div className="flex justify-between items-center">
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-4 w-12" />
          </div>
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-6 w-2/3" />
          <Skeleton className="h-8 w-20" />
        </div>
      </Card>
    );
  }

  return (
    <motion.div
      ref={cardRef}
      className={cn("group relative", className)}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsHovered(true)}
      onBlur={() => setIsHovered(false)}
      tabIndex={0}
      role="article"
      aria-labelledby={`product-${id}-title`}
      aria-describedby={`product-${id}-description`}
    >
      <Card className="overflow-hidden backdrop-blur-md bg-card border border-border shadow-lg transition-all duration-300 group-hover:shadow-xl group-focus:shadow-xl group-hover:border-primary/50 group-focus:border-primary/50">
        {/* Image Container */}
        <div className="relative overflow-hidden aspect-square">
          <motion.img
            src={image || "/placeholder.svg"}
            alt={name}
            className="w-full h-full object-cover"
            animate={{
              scale: isHovered ? 1.05 : 1,
            }}
            transition={{ duration: 0.3 }}
          />
          
          {/* Gradient Overlay */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"
            animate={{
              opacity: isHovered ? 1 : 0,
            }}
            transition={{ duration: 0.3 }}
          />

          {/* Discount Badge */}
          {discount && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute top-3 left-3 bg-destructive text-destructive-foreground px-2 py-1 rounded-md text-xs font-bold"
            >
              {discount}
            </motion.div>
          )}

          {/* Action Buttons */}
          <div className="absolute top-3 right-3 flex flex-col gap-2">
            <Button
              size="sm"
              variant={isLiked ? "default" : "secondary"}
              onClick={(e) => {
                e.stopPropagation();
                onLike?.(id);
              }}
              className="p-2 h-auto"
              aria-label={isLiked ? "Remove from favorites" : "Add to favorites"}
            >
              <Heart className={cn("w-4 h-4", isLiked && "fill-current")} />
            </Button>

            <Button
              size="sm"
              variant="secondary"
              className="p-2 h-auto"
              aria-label="Quick view product"
            >
              <Eye className="w-4 h-4" />
            </Button>
          </div>

          {/* Hover Actions */}
          <AnimatePresence>
            {isHovered && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="absolute bottom-4 left-4 right-4 flex gap-2"
              >
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    onAddToCart?.(id);
                  }}
                  className="flex-1"
                  size="sm"
                >
                  <ShoppingCart className="w-4 h-4 mr-2" />
                  Add to Cart
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Content Section */}
        <div className="p-4 space-y-3">
          {/* Store and Rating */}
          <div className="flex items-center justify-between">
            <Badge variant="secondary" className="text-xs">
              {store}
            </Badge>
            
            <div className="flex items-center gap-1 text-sm">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <span className="font-medium">{rating}</span>
              <span className="text-muted-foreground">({reviewCount})</span>
            </div>
          </div>

          {/* Product Name */}
          <h3 
            id={`product-${id}-title`}
            className="font-semibold text-lg leading-tight line-clamp-2 group-hover:text-primary transition-colors"
          >
            {name}
          </h3>

          {/* Price and Value Score */}
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-primary">
                  {price}
                </span>
                {originalPrice && (
                  <span className="text-sm text-muted-foreground line-through">
                    {originalPrice}
                  </span>
                )}
              </div>
            </div>

            {/* Value Score with dual encoding */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1">
                <Star 
                  className={cn(
                    "w-4 h-4",
                    getScoreColor(valueScore)
                  )} 
                />
                <span className="font-medium">{valueScore}</span>
                <span className="text-xs text-muted-foreground">/5</span>
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="p-1 h-auto"
                aria-label="Value score explanation"
              >
                <Info className="w-3 h-3" />
              </Button>
            </div>
          </div>

          {/* Progressive Spec Disclosure */}
          <div 
            id={`product-${id}-description`}
            className="space-y-2"
          >
            <div className="text-sm text-muted-foreground">
              {specs.slice(0, 2).map((spec, index) => (
                <span key={index}>
                  {spec}
                  {index < 1 && specs.length > 1 && " · "}
                </span>
              ))}
            </div>

            <AnimatePresence>
              {showAllSpecs && specs.length > 2 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="text-sm text-muted-foreground"
                >
                  {specs.slice(2).map((spec, index) => (
                    <div key={index + 2}>{spec}</div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>

            {specs.length > 2 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAllSpecs(!showAllSpecs)}
                className="p-0 h-auto text-xs text-primary hover:text-primary/80"
              >
                {showAllSpecs ? (
                  <>
                    Show less <ChevronUp className="w-3 h-3 ml-1" />
                  </>
                ) : (
                  <>
                    Show more specs <ChevronDown className="w-3 h-3 ml-1" />
                  </>
                )}
              </Button>
            )}
          </div>

          {/* Always-visible Compare Button */}
          <div className="pt-2 border-t border-border">
            <Button
              variant={isComparing ? "default" : "outline"}
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onCompare?.(id);
              }}
              className="w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              {isComparing ? "Remove from Compare" : "Compare"}
            </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export { ValueScoredProductCard };
