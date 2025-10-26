/**
 * Sentiment Panel Component
 * Shows sentiment analysis for products
 */

import React, { useEffect, useState, useCallback } from 'react';
import { MessageCircle, ThumbsUp, ThumbsDown, Meh } from 'lucide-react';
import { useAnalytics } from '../../hooks/useAnalytics';
import { SentimentAnalysis } from '../../types/alerts';

interface SentimentPanelProps {
  productId: number;
}

export const SentimentPanel: React.FC<SentimentPanelProps> = ({ productId }) => {
  const [sentiment, setSentiment] = useState<SentimentAnalysis | null>(null);
  const { getSentiment, loading, error } = useAnalytics();

  const loadSentiment = useCallback(async () => {
    const data = await getSentiment(productId);
    if (data) setSentiment(data);
  }, [getSentiment, productId]);

  useEffect(() => {
    loadSentiment();
  }, [loadSentiment]);

  const getSentimentIcon = (label: string) => {
    switch (label) {
      case 'positive':
        return <ThumbsUp className="h-8 w-8 text-green-600" />;
      case 'negative':
        return <ThumbsDown className="h-8 w-8 text-red-600" />;
      default:
        return <Meh className="h-8 w-8 text-yellow-600" />;
    }
  };

  const getSentimentColor = (label: string) => {
    switch (label) {
      case 'positive':
        return 'bg-green-50 border-green-200';
      case 'negative':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-yellow-50 border-yellow-200';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <MessageCircle className="h-6 w-6 text-blue-600" />
        <h2 className="text-xl font-bold text-gray-900">Customer Sentiment</h2>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      ) : !sentiment ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <MessageCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No sentiment data available</p>
        </div>
      ) : (
        <div>
          {/* Overall Sentiment */}
          <div className={`border rounded-lg p-6 mb-6 ${getSentimentColor(sentiment.overall_sentiment.label)}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {getSentimentIcon(sentiment.overall_sentiment.label)}
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 capitalize mb-1">
                    {sentiment.overall_sentiment.label}
                  </h3>
                  <p className="text-sm text-gray-600">
                    Based on {sentiment.total_reviews} reviews
                  </p>
                </div>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-gray-900">
                  {sentiment.overall_sentiment.score.toFixed(1)}
                </p>
                <p className="text-sm text-gray-600">Score</p>
              </div>
            </div>
          </div>

          {/* Sentiment Distribution */}
          <div className="mb-6">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Sentiment Distribution</h4>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <ThumbsUp className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium text-gray-700">Positive</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {sentiment.positive_count ?? 0} ({((sentiment.positive_count ?? 0 / sentiment.total_reviews) * 100).toFixed(0)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${((sentiment.positive_count ?? 0 / sentiment.total_reviews) * 100)}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Meh className="h-4 w-4 text-yellow-600" />
                    <span className="text-sm font-medium text-gray-700">Neutral</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {sentiment.neutral_count ?? 0} ({((sentiment.neutral_count ?? 0 / sentiment.total_reviews) * 100).toFixed(0)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-yellow-600 h-2 rounded-full"
                    style={{ width: `${((sentiment.neutral_count ?? 0 / sentiment.total_reviews) * 100)}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <ThumbsDown className="h-4 w-4 text-red-600" />
                    <span className="text-sm font-medium text-gray-700">Negative</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {sentiment.negative_count ?? 0} ({((sentiment.negative_count ?? 0 / sentiment.total_reviews) * 100).toFixed(0)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-600 h-2 rounded-full"
                    style={{ width: `${((sentiment.negative_count ?? 0 / sentiment.total_reviews) * 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Key Topics/Keywords */}
          {sentiment.key_topics && sentiment.key_topics.length > 0 && (
            <div className="mb-6">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Key Topics</h4>
              <div className="flex flex-wrap gap-2">
                {sentiment.key_topics.map((topic, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Sample Reviews */}
          {sentiment.sample_reviews && sentiment.sample_reviews.length > 0 && (
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Sample Reviews</h4>
              <div className="space-y-3">
                {sentiment.sample_reviews.slice(0, 5).map((review, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0">
                        {review.sentiment === 'positive' ? (
                          <ThumbsUp className="h-5 w-5 text-green-600" />
                        ) : review.sentiment === 'negative' ? (
                          <ThumbsDown className="h-5 w-5 text-red-600" />
                        ) : (
                          <Meh className="h-5 w-5 text-yellow-600" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-900">{review.text}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className={`text-xs px-2 py-1 rounded-full capitalize ${
                            review.sentiment === 'positive' ? 'bg-green-100 text-green-700' :
                            review.sentiment === 'negative' ? 'bg-red-100 text-red-700' :
                            'bg-yellow-100 text-yellow-700'
                          }`}>
                            {review.sentiment}
                          </span>
                          <span className="text-xs text-gray-600">
                            Confidence: {(review.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
