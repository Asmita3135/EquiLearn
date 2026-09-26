export type FileCategory = 'pdf' | 'image' | 'video' | 'audio' | 'text' | 'unsupported';

export type UploadStatus = 'IDLE' | 'READY' | 'ERROR' | 'PROCESSING' | 'COMPLETED_PLACEHOLDER';

export interface FileValidationResult {
  isValid: boolean;
  category: FileCategory;
  categoryLabel: string;
  explanation: string;
  errorMessage?: string;
  formattedSize: string;
}

export const SUPPORTED_EXTENSIONS = [
  '.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp',
  '.mp4', '.mov', '.avi', '.mp3', '.wav', '.m4a', '.txt'
];

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function validateFile(file: File): FileValidationResult {
  const extension = `.${file.name.split('.').pop()?.toLowerCase()}`;
  const formattedSize = formatFileSize(file.size);

  if (!SUPPORTED_EXTENSIONS.includes(extension)) {
    return {
      isValid: false,
      category: 'unsupported',
      categoryLabel: 'Unsupported File Type',
      explanation: 'Unsupported format.',
      errorMessage: `Unsupported file type "${extension}". Please select a valid document, image, audio, or video file.`,
      formattedSize
    };
  }

  if (extension === '.pdf') {
    return {
      isValid: true,
      category: 'pdf',
      categoryLabel: 'PDF Document',
      explanation: 'PDF will be processed by Member 1 Vision & Member 3 NLP for accessible text & visual representations.',
      formattedSize
    };
  }

  if (['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'].includes(extension)) {
    return {
      isValid: true,
      category: 'image',
      categoryLabel: 'Image Document',
      explanation: 'Image will be processed by Member 1 OCR/VLM & Member 3 NLP for accessible representations.',
      formattedSize
    };
  }

  if (['.mp4', '.mov', '.avi'].includes(extension)) {
    return {
      isValid: true,
      category: 'video',
      categoryLabel: 'Video File',
      explanation: 'Video will be processed by Member 2 Audio Extraction, Whisper ASR, and gTTS.',
      formattedSize
    };
  }

  if (['.mp3', '.wav', '.m4a'].includes(extension)) {
    return {
      isValid: true,
      category: 'audio',
      categoryLabel: 'Audio Recording',
      explanation: 'Audio will be processed by Member 2 Whisper ASR, Timestamping, and gTTS.',
      formattedSize
    };
  }

  if (extension === '.txt') {
    return {
      isValid: true,
      category: 'text',
      categoryLabel: 'Text Document',
      explanation: 'Text will be processed for simplified reading and multi-profile representations.',
      formattedSize
    };
  }

  return {
    isValid: false,
    category: 'unsupported',
    categoryLabel: 'Unknown Type',
    explanation: 'Unsupported format.',
    errorMessage: 'Unsupported file type selected.',
    formattedSize
  };
}
