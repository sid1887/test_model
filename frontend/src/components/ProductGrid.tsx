import { Product } from '@/api/types';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ExternalLink, TrendingUp, TrendingDown } from 'lucide-react';

interface ProductGridProps {
  products: Product[];
}

export function ProductGrid({ products }: ProductGridProps) {
  if (!products || products.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No products found</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}

interface ProductCardProps {
  product: Product;
}

function ProductCard({ product }: ProductCardProps) {
  const discountPercent = product.original_price
    ? Math.round(((product.original_price - product.current_price) / product.original_price) * 100)
    : 0;

  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      <CardHeader className="p-0">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-48 object-cover"
          />
        ) : (
          <div className="w-full h-48 bg-muted flex items-center justify-center">
            <span className="text-muted-foreground">No image</span>
          </div>
        )}
        {discountPercent > 0 && (
          <Badge className="absolute top-2 right-2 bg-red-500">
            -{discountPercent}%
          </Badge>
        )}
        {!product.in_stock && (
          <Badge className="absolute top-2 left-2 bg-gray-500">
            Out of Stock
          </Badge>
        )}
      </CardHeader>

      <CardContent className="p-4">
        <h3 className="font-semibold line-clamp-2 mb-2">{product.name}</h3>
        
        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-2xl font-bold">
            ${product.current_price.toFixed(2)}
          </span>
          {product.original_price && product.original_price > product.current_price && (
            <span className="text-sm line-through text-muted-foreground">
              ${product.original_price.toFixed(2)}
            </span>
          )}
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">{product.retailer}</span>
          {product.rating && (
            <span className="flex items-center gap-1">
              ⭐ {product.rating.toFixed(1)}
              {product.reviews_count && (
                <span className="text-muted-foreground">
                  ({product.reviews_count})
                </span>
              )}
            </span>
          )}
        </div>

        {product.category && (
          <Badge variant="outline" className="mt-2">
            {product.category}
          </Badge>
        )}
      </CardContent>

      <CardFooter className="p-4 pt-0 flex gap-2">
        <Button
          variant="default"
          className="flex-1"
          asChild
          disabled={!product.in_stock}
        >
          <a
            href={product.product_url}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            View Deal
          </a>
        </Button>
        
        <Button
          variant="outline"
          size="icon"
          onClick={() => window.location.href = `/product/${product.id}`}
        >
          {discountPercent > 0 ? (
            <TrendingDown className="h-4 w-4 text-green-500" />
          ) : (
            <TrendingUp className="h-4 w-4" />
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}

export default ProductGrid;
