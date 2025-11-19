import React, { useEffect, useState } from 'react';
import { useRecommendations, useSimilarProducts, useTrendingProducts, useForecastDemand } from '@/api/hooks';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { TrendingUp, Zap, Target } from 'lucide-react';

interface RecommendationsPanelProps {
  userId?: string;
  productId?: string;
}

interface Recommendation {
  product_id: string;
  name: string;
  price?: number;
  image?: string;
  score?: number;
  reason?: string;
}

interface DemandForecast {
  product_id: string;
  forecast: Array<{
    date: string;
    predicted_demand: number;
    confidence: number;
  }>;
}

export function RecommendationsPanel({ userId, productId }: RecommendationsPanelProps) {
  const { data: userRecs, isLoading: isLoadingUser } = useRecommendations(userId || '', !!userId);
  const { data: similarProds, isLoading: isLoadingSimilar } = useSimilarProducts(productId || '', !!productId);
  const { data: trending } = useTrendingProducts();
  const { data: forecast } = useForecastDemand(productId || '', !!productId);

  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [demandForecast, setDemandForecast] = useState<DemandForecast | null>(null);

  useEffect(() => {
    if (userRecs?.products) {
      setRecommendations(userRecs.products);
    }
  }, [userRecs]);

  useEffect(() => {
    if (forecast) {
      setDemandForecast(forecast);
    }
  }, [forecast]);

  const renderProductCard = (product: Recommendation) => (
    <div key={product.product_id} className="p-4 border rounded-lg hover:shadow-lg transition-shadow">
      {product.image && (
        <img src={product.image} alt={product.name} className="w-full h-40 object-cover rounded mb-2" />
      )}
      <h4 className="font-semibold text-sm truncate">{product.name}</h4>
      <div className="flex justify-between items-center mt-2">
        {product.price && <span className="text-lg font-bold">${product.price}</span>}
        {product.score && (
          <Badge variant="secondary" className="text-xs">
            {(product.score * 100).toFixed(0)}% match
          </Badge>
        )}
      </div>
      {product.reason && <p className="text-xs text-gray-600 mt-1">{product.reason}</p>}
    </div>
  );

  return (
    <div className="w-full">
      <Tabs defaultValue="for-you" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="for-you" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            <span className="hidden sm:inline">For You</span>
          </TabsTrigger>
          <TabsTrigger value="similar" className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            <span className="hidden sm:inline">Similar</span>
          </TabsTrigger>
          <TabsTrigger value="trending" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            <span className="hidden sm:inline">Trending</span>
          </TabsTrigger>
          <TabsTrigger value="forecast">Forecast</TabsTrigger>
        </TabsList>

        {/* For You Recommendations */}
        <TabsContent value="for-you" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Personalized Recommendations</CardTitle>
              <CardDescription>Based on your browsing and purchase history</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingUser ? (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {[...Array(8)].map((_, i) => (
                    <Skeleton key={i} className="h-40" />
                  ))}
                </div>
              ) : recommendations.length > 0 ? (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {recommendations.slice(0, 12).map(renderProductCard)}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  {userId ? 'No recommendations yet' : 'Sign in to get personalized recommendations'}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Similar Products */}
        <TabsContent value="similar" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Similar Products</CardTitle>
              <CardDescription>You might also like</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingSimilar ? (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {[...Array(8)].map((_, i) => (
                    <Skeleton key={i} className="h-40" />
                  ))}
                </div>
              ) : similarProds?.products && similarProds.products.length > 0 ? (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {similarProds.products.map(renderProductCard)}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  {productId ? 'No similar products found' : 'Select a product to see similar items'}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Trending Products */}
        <TabsContent value="trending" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Trending Now</CardTitle>
              <CardDescription>Popular products right now</CardDescription>
            </CardHeader>
            <CardContent>
              {!trending ? (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {[...Array(8)].map((_, i) => (
                    <Skeleton key={i} className="h-40" />
                  ))}
                </div>
              ) : trending.products && trending.products.length > 0 ? (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
                  {trending.products.map(renderProductCard)}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">No trending products</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Demand Forecast */}
        <TabsContent value="forecast" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Demand Forecast</CardTitle>
              <CardDescription>Predicted demand for next 7 days</CardDescription>
            </CardHeader>
            <CardContent>
              {!demandForecast ? (
                <div className="text-center py-8 text-gray-500">
                  {productId ? 'Loading forecast...' : 'Select a product to see demand forecast'}
                </div>
              ) : (
                <div className="space-y-4">
                  {demandForecast.forecast?.map((day, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 border rounded">
                      <div>
                        <p className="font-semibold text-sm">{day.date}</p>
                        <p className="text-xs text-gray-600">Predicted Demand</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold">{day.predicted_demand}</p>
                        <Badge variant="outline" className="mt-1">
                          {(day.confidence * 100).toFixed(0)}% confidence
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
