// React Query hooks for AI API
import { useMutation } from '@tanstack/react-query';
import { aiAPI } from '@/services/api';
import type {
  ImageUploadResponse,
  ImageAnalysisResponse,
  ImageAnalysisRequest,
  CLIPResult,
  CLIPCompareRequest,
  BarcodeResult,
  BarcodeDecodeRequest,
  OCRReceiptResponse,
  OCRReceiptRequest,
  TextGenerationRequest,
  TextGenerationResponse,
  TextAnalysisRequest,
  TextAnalysisResponse,
  EmbeddingsRequest,
  EmbeddingsResponse,
  VoiceTranscriptionResponse,
  CaptchaSolveRequest,
  CaptchaSolveResponse,
} from '@/services/api/ai';
import { toast } from 'sonner';

/**
 * Upload image
 */
export const useUploadImage = () => {
  return useMutation<ImageUploadResponse, Error, File>({
    mutationFn: (file: File) => aiAPI.uploadImage(file),
    onSuccess: () => {
      toast.success('Image uploaded successfully!');
    },
  });
};

/**
 * Analyze image
 */
export const useAnalyzeImage = () => {
  return useMutation<ImageAnalysisResponse, Error, ImageAnalysisRequest>({
    mutationFn: (request: ImageAnalysisRequest) => aiAPI.analyzeImage(request),
    onSuccess: () => {
      toast.success('Image analyzed successfully!');
    },
  });
};

/**
 * CLIP compare images
 */
export const useCLIPCompare = () => {
  return useMutation<CLIPResult[], Error, CLIPCompareRequest>({
    mutationFn: (request: CLIPCompareRequest) => aiAPI.clipCompare(request),
  });
};

/**
 * Decode barcode
 */
export const useDecodeBarcode = () => {
  return useMutation<BarcodeResult, Error, BarcodeDecodeRequest>({
    mutationFn: (request: BarcodeDecodeRequest) => aiAPI.decodeBarcode(request),
    onSuccess: (data) => {
      if (data.detected && data.barcode_value) {
        toast.success(`Barcode detected: ${data.barcode_value}`);
      }
    },
  });
};

/**
 * Extract receipt (OCR)
 */
export const useExtractReceipt = () => {
  return useMutation<OCRReceiptResponse, Error, OCRReceiptRequest>({
    mutationFn: (request: OCRReceiptRequest) => aiAPI.extractReceipt(request),
    onSuccess: (data) => {
      toast.success(`Receipt extracted: ${data.items.length} items found`);
    },
  });
};

/**
 * Generate text with LLM
 */
export const useGenerateText = () => {
  return useMutation<TextGenerationResponse, Error, TextGenerationRequest>({
    mutationFn: (request: TextGenerationRequest) => aiAPI.generateText(request),
  });
};

/**
 * Analyze text sentiment/classification
 */
export const useAnalyzeText = () => {
  return useMutation<TextAnalysisResponse, Error, TextAnalysisRequest>({
    mutationFn: (request: TextAnalysisRequest) => aiAPI.analyzeText(request),
  });
};

/**
 * Get embeddings for text
 */
export const useGetEmbeddings = () => {
  return useMutation<EmbeddingsResponse, Error, EmbeddingsRequest>({
    mutationFn: (request: EmbeddingsRequest) => aiAPI.getEmbeddings(request),
  });
};

/**
 * Transcribe voice to text
 */
export const useTranscribeVoice = () => {
  return useMutation<VoiceTranscriptionResponse, Error, Blob>({
    mutationFn: (audioBlob: Blob) => aiAPI.transcribeVoice(audioBlob),
    onSuccess: () => {
      toast.success('Voice transcribed successfully!');
    },
  });
};

/**
 * Solve CAPTCHA
 */
export const useSolveCaptcha = () => {
  return useMutation<CaptchaSolveResponse, Error, CaptchaSolveRequest>({
    mutationFn: (request: CaptchaSolveRequest) => aiAPI.solveCaptcha(request),
    onSuccess: () => {
      toast.success('CAPTCHA solved!');
    },
  });
};
