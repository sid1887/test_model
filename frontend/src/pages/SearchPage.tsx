import { useState, useRef } from 'react';
import { Search, TrendingUp, Zap, ImagePlus, Mic, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useUnifiedSearchV2, useImageSearchV2, useVoiceSearchV2 } from '@/hooks/api';
import { toast } from 'sonner';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Text search with God Engine V2 - REAL backend integration!
  const { data: searchResults, isLoading, error } = useUnifiedSearchV2(
    searchTerm,
    {
      top_k: 20,
      cache_level: 'both',
      enrich: true,
      use_faiss: true,
    }
  );

  // Image search V2
  const imageSearch = useImageSearchV2();
  
  // Voice search V2
  const voiceSearch = useVoiceSearchV2();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      setSearchTerm(query.trim());
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        
        toast.loading('Transcribing audio with Whisper...');
        
        try {
          const result = await voiceSearch.mutateAsync(audioBlob);
          toast.success('Audio transcribed!');
          setQuery(result.transcription);
          setSearchTerm(result.transcription);
        } catch (error) {
          toast.error('Failed to transcribe audio');
          console.error(error);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      toast.info('Recording... Click again to stop');
    } catch (error) {
      toast.error('Microphone access denied');
      console.error(error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    toast.loading('Analyzing image with CLIP...');

    try {
      const result = await imageSearch.mutateAsync({
        file,
        top_k: 20,
      });

      toast.success('Image analyzed successfully!');
      // Use first search result as query if available
      if (result.search_results && result.search_results.length > 0) {
        setSearchTerm(result.search_results[0].title);
      }
    } catch (error) {
      toast.error('Failed to analyze image');
      console.error(error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
          Cumpair - God Engine
        </h1>
        <p className="text-xl text-muted-foreground mb-8">
          AI-powered price comparison across thousands of retailers
        </p>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="max-w-2xl mx-auto">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-5 w-5" />
              <Input
                type="text"
                placeholder="Search for products... (e.g., iPhone 15, MacBook Pro)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-10 h-12 text-lg"
              />
            </div>
            <Button type="submit" size="lg" className="h-12 px-8">
              <Zap className="mr-2 h-5 w-5" />
              Search
            </Button>
            <Button 
              type="button" 
              size="lg" 
              variant={isRecording ? "destructive" : "outline"}
              className="h-12 px-6"
              onClick={toggleRecording}
            >
              {isRecording ? <Square className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
            </Button>
          </div>
        </form>

        {/* Image Search */}
        <div className="mt-4 max-w-2xl mx-auto">
          <label className="cursor-pointer">
            <div className="border-2 border-dashed border-muted-foreground/30 rounded-lg p-4 hover:border-muted-foreground/60 transition-colors">
              <ImagePlus className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Or upload an image to search visually
              </p>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </div>
          </label>
        </div>
      </div>

      {/* Features */}
      {!searchTerm && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                Lightning Fast
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Multi-tier caching with &lt;200ms response times. Ghost results for instant UX.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-500" />
                AI-Powered
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                10+ AI models analyze products, prices, and trends in real-time.
              </CardDescription>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ImagePlus className="h-5 w-5 text-blue-500" />
                Visual Search
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>
                Upload product images. CLIP + barcode + OCR for accurate matching.
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search Results */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="mt-4 text-muted-foreground">Searching across retailers...</p>
        </div>
      )}

      {error && (
        <div className="text-center py-12">
          <p className="text-red-500">Error: {error.message}</p>
        </div>
      )}

      {searchResults && (
        <div className="space-y-6">
          {/* Search Metadata */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">
                {searchResults.total_results} Results for "{searchTerm}"
              </h2>
              <div className="flex gap-4 mt-2 text-sm text-muted-foreground">
                {searchResults.cache_info.hit && (
                  <span className="flex items-center gap-1">
                    <Zap className="h-4 w-4 text-yellow-500" />
                    Cache Hit ({searchResults.cache_info.level})
                  </span>
                )}
                {searchResults.enriched && (
                  <span className="text-purple-500">✨ AI Enriched</span>
                )}
                <span>{searchResults.results.length} shown</span>
              </div>
            </div>
          </div>

          {/* Search Results */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {searchResults.results.map((result) => (
              <Card key={result.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-4">
                  {result.image_url && (
                    <img
                      src={result.image_url}
                      alt={result.title}
                      className="w-full h-48 object-cover rounded-md mb-3"
                    />
                  )}
                  <h3 className="font-semibold text-lg mb-2 line-clamp-2">
                    {result.title}
                  </h3>
                  {result.description && (
                    <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                      {result.description}
                    </p>
                  )}
                  <div className="space-y-2">
                    {result.price && (
                      <div className="flex items-center justify-between">
                        <span className="text-2xl font-bold text-primary">
                          ${result.price.toFixed(2)}
                        </span>
                        {result.similarity_score && (
                          <span className="text-xs text-muted-foreground">
                            {(result.similarity_score * 100).toFixed(0)}% match
                          </span>
                        )}
                      </div>
                    )}
                    {result.retailer && (
                      <p className="text-sm text-muted-foreground">{result.retailer}</p>
                    )}
                    {result.in_stock !== undefined && (
                      <span className={`text-xs font-medium ${result.in_stock ? 'text-green-600' : 'text-red-600'}`}>
                        {result.in_stock ? '✓ In Stock' : '✗ Out of Stock'}
                      </span>
                    )}
                    {result.category && (
                      <span className="text-xs bg-secondary px-2 py-1 rounded">
                        {result.category}
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
