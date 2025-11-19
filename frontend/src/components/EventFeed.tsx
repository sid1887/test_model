import React, { useEffect, useState } from 'react';
import { useUserEvents } from '@/api/hooks';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertCircle, Check, Package, DollarSign, Bell } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface EventFeedProps {
  userId?: string;
  limit?: number;
}

interface Event {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  data?: Record<string, unknown>;
  read?: boolean;
}

const eventIcons: Record<string, React.ReactNode> = {
  'product.created': <Package className="w-4 h-4" />,
  'price.changed': <DollarSign className="w-4 h-4" />,
  'price_alert.triggered': <Bell className="w-4 h-4" />,
  'purchase.completed': <Check className="w-4 h-4" />,
  'recommendation.generated': <AlertCircle className="w-4 h-4" />,
};

const eventColors: Record<string, string> = {
  'product.created': 'bg-blue-100 text-blue-800',
  'price.changed': 'bg-yellow-100 text-yellow-800',
  'price_alert.triggered': 'bg-orange-100 text-orange-800',
  'purchase.completed': 'bg-green-100 text-green-800',
  'recommendation.generated': 'bg-purple-100 text-purple-800',
};

export function EventFeed({ userId, limit = 20 }: EventFeedProps) {
  const { data: eventsData, isLoading } = useUserEvents(userId || '', !!userId);
  const [events, setEvents] = useState<Event[]>([]);

  useEffect(() => {
    if (eventsData?.events) {
      setEvents(eventsData.events.slice(0, limit));
    }
  }, [eventsData, limit]);

  const formatEventType = (type: string): string => {
    return type
      .split('.')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getEventMessage = (event: Event): string => {
    const eventType = event.type;
    const data = event.data || {};

    switch (eventType) {
      case 'price.changed':
        return `Price changed from $${data.old_price} to $${data.new_price}`;
      case 'price_alert.triggered':
        return `Price alert triggered: ${data.product_name} is now $${data.price}`;
      case 'product.created':
        return `New product added: ${data.product_name}`;
      case 'purchase.completed':
        return `Purchase completed: ${data.product_name} × ${data.quantity}`;
      case 'recommendation.generated':
        return `New recommendation: ${data.recommendation_reason}`;
      default:
        return event.description || formatEventType(eventType);
    }
  };

  if (!userId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Event Feed</CardTitle>
          <CardDescription>Sign in to see your event feed</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Event Feed</CardTitle>
        <CardDescription>Real-time updates and notifications</CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-96 pr-4">
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-20 bg-gray-100 rounded animate-pulse" />
              ))}
            </div>
          ) : events.length > 0 ? (
            <div className="space-y-3">
              {events.map((event) => (
                <div
                  key={event.id}
                  className="flex gap-3 p-3 rounded-lg border hover:shadow-sm transition-shadow bg-white"
                >
                  <div className={`p-2 rounded-full flex-shrink-0 ${eventColors[event.type] || 'bg-gray-100'}`}>
                    {eventIcons[event.type] || <AlertCircle className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold text-sm">{formatEventType(event.type)}</p>
                        <p className="text-xs text-gray-600 mt-1">{getEventMessage(event)}</p>
                      </div>
                      <Badge variant="outline" className="flex-shrink-0 text-xs">
                        {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No events yet</p>
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
