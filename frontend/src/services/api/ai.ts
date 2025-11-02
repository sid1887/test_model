// AI Features API Service - Image analysis, text generation, embeddings, voice
// /api/images/*, /api/clip/*, /api/barcode/*, /api/ocr/*, /api/text/*, /api/embeddings/*, /api/voice/*

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ==================== TYPES ====================

export interface ImageUploadResponse {
  image_id: string;
  filename: string;
  file_path: string;
  uploaded_at: string;
}

export interface ImageAnalysisRequest {
  image_id?: string;
  image_url?: string;
  base64_image?: string;
  tasks: ('clip' | 'barcode' | 'ocr' | 'caption' | 'objects')[];
}

export interface ImageAnalysisResponse {
  image_id: string;
  clip_results?: CLIPResult[];
  barcode?: BarcodeResult;
  ocr_text?: string;
  caption?: string;
  objects?: DetectedObject[];
  processing_time: number;
}

export interface CLIPResult {
  product_id: string;
  title: string;
  image_url?: string;
  similarity_score: number;
  price?: number;
  retailer?: string;
}

export interface BarcodeResult {
  detected: boolean;
  barcode_type?: string; // 'EAN13', 'UPC-A', 'QR', etc.
  barcode_value?: string;
  confidence: number;
  bounding_box?: { x: number; y: number; width: number; height: number };
}

export interface DetectedObject {
  label: string;
  confidence: number;
  bounding_box: { x: number; y: number; width: number; height: number };
}

export interface CLIPCompareRequest {
  image_id?: string;
  image_url?: string;
  base64_image?: string;
  top_k?: number;
}

export interface BarcodeDecodeRequest {
  image_id?: string;
  image_url?: string;
  base64_image?: string;
}

export interface OCRReceiptRequest {
  image_id?: string;
  image_url?: string;
  base64_image?: string;
}

export interface OCRReceiptResponse {
  text: string;
  items: {
    name: string;
    quantity?: number;
    unit_price?: number;
    total_price?: number;
  }[];
  total_amount?: number;
  currency?: string;
  merchant?: string;
  date?: string;
  confidence: number;
}

export interface TextGenerationRequest {
  prompt: string;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
  model?: string;
}

export interface TextGenerationResponse {
  generated_text: string;
  model: string;
  tokens_used: number;
  generation_time: number;
}

export interface TextAnalysisRequest {
  text: string;
  tasks: ('sentiment' | 'ner' | 'summarize' | 'keywords')[];
}

export interface TextAnalysisResponse {
  sentiment?: {
    label: 'positive' | 'neutral' | 'negative';
    score: number;
  };
  entities?: {
    text: string;
    type: string; // 'PERSON', 'ORG', 'PRODUCT', etc.
    confidence: number;
  }[];
  summary?: string;
  keywords?: { word: string; score: number }[];
}

export interface EmbeddingsRequest {
  texts: string[];
  model?: string;
}

export interface EmbeddingsResponse {
  embeddings: number[][];
  model: string;
  dimension: number;
}

export interface VoiceTranscriptionRequest {
  audio: Blob;
  language?: string;
}

export interface VoiceTranscriptionResponse {
  transcription: string;
  language: string;
  confidence: number;
  duration: number;
  segments?: {
    text: string;
    start: number;
    end: number;
  }[];
}

export interface CaptchaSolveRequest {
  image_url?: string;
  base64_image?: string;
}

export interface CaptchaSolveResponse {
  solution: string;
  confidence: number;
  solve_time: number;
}

// ==================== HELPER FUNCTIONS ====================

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || error.message || 'Request failed');
  }

  return response.json();
}

// ==================== API FUNCTIONS - IMAGES ====================

/**
 * Upload image for processing
 * POST /api/images/upload
 */
export const uploadImage = async (file: File): Promise<ImageUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/images/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
};

/**
 * Analyze image with multiple AI tasks
 * POST /api/images/analyze
 */
export const analyzeImage = async (
  request: ImageAnalysisRequest
): Promise<ImageAnalysisResponse> => {
  return fetchJSON<ImageAnalysisResponse>('/api/images/analyze', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

// ==================== API FUNCTIONS - CLIP ====================

/**
 * Find similar products using CLIP visual similarity
 * POST /api/clip/compare
 */
export const clipCompare = async (request: CLIPCompareRequest): Promise<CLIPResult[]> => {
  return fetchJSON<CLIPResult[]>('/api/clip/compare', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

// ==================== API FUNCTIONS - BARCODE ====================

/**
 * Decode barcode from image
 * POST /api/barcode/decode
 */
export const decodeBarcode = async (request: BarcodeDecodeRequest): Promise<BarcodeResult> => {
  return fetchJSON<BarcodeResult>('/api/barcode/decode', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

// ==================== API FUNCTIONS - OCR ====================

/**
 * Extract text from receipt image
 * POST /api/ocr/receipt
 */
export const extractReceipt = async (request: OCRReceiptRequest): Promise<OCRReceiptResponse> => {
  return fetchJSON<OCRReceiptResponse>('/api/ocr/receipt', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

// ==================== API FUNCTIONS - TEXT ====================

/**
 * Generate text using HuggingFace LLM
 * POST /api/text/generate
 */
export const generateText = async (
  request: TextGenerationRequest
): Promise<TextGenerationResponse> => {
  return fetchJSON<TextGenerationResponse>('/api/text/generate', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * Analyze text (sentiment, NER, summarization, keywords)
 * POST /api/text/analyze
 */
export const analyzeText = async (request: TextAnalysisRequest): Promise<TextAnalysisResponse> => {
  return fetchJSON<TextAnalysisResponse>('/api/text/analyze', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

// ==================== API FUNCTIONS - EMBEDDINGS ====================

/**
 * Get text embeddings for similarity search
 * POST /api/embeddings
 */
export const getEmbeddings = async (request: EmbeddingsRequest): Promise<EmbeddingsResponse> => {
  return fetchJSON<EmbeddingsResponse>('/api/embeddings', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

// ==================== API FUNCTIONS - VOICE ====================

/**
 * Transcribe audio to text using Whisper
 * POST /api/voice/transcribe
 */
export const transcribeVoice = async (
  audio: Blob,
  language?: string
): Promise<VoiceTranscriptionResponse> => {
  const formData = new FormData();
  formData.append('file', audio, 'audio.webm');
  if (language) {
    formData.append('language', language);
  }

  const response = await fetch(`${API_BASE_URL}/api/voice/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Transcription failed');
  }

  return response.json();
};

// ==================== API FUNCTIONS - CAPTCHA ====================

/**
 * Solve CAPTCHA using self-hosted service
 * POST /api/captcha/solve
 */
export const solveCaptcha = async (request: CaptchaSolveRequest): Promise<CaptchaSolveResponse> => {
  return fetchJSON<CaptchaSolveResponse>('/api/captcha/solve', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

// ==================== EXPORT ====================

export const aiAPI = {
  // Images
  uploadImage,
  analyzeImage,
  
  // CLIP
  clipCompare,
  
  // Barcode
  decodeBarcode,
  
  // OCR
  extractReceipt,
  
  // Text
  generateText,
  analyzeText,
  
  // Embeddings
  getEmbeddings,
  
  // Voice
  transcribeVoice,
  
  // CAPTCHA
  solveCaptcha,
};

export default aiAPI;
