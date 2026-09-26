import type { LessonData } from '../types/lesson';
import type { ProfileId } from '../types/profile';
import { API_BASE_URL } from './audioSpeech';

export interface DocumentRepresentation {
  primary_text?: string;
  secondary_text?: string;
  summary?: string;
  visual_descriptions?: string[];
  key_terms?: string[];
  tts_ready_text?: string;
  metadata?: any;
}

export interface DocumentPipelineResult {
  status: string;
  document_id: string;
  extracted_text: string;
  summary: string;
  alt_text: string;
  visual_descriptions: string[];
  key_terms: string[];
  representations: Record<string, DocumentRepresentation>;
  evaluation_metrics?: any;
  metadata?: any;
}

export async function processDocumentApi(file: File): Promise<DocumentPipelineResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/v1/process-document`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }

  const data = await response.json();
  return data;
}

export function convertDocumentResultToLessonData(
  file: File,
  result: DocumentPipelineResult,
  selectedProfile?: ProfileId | null
): LessonData {
  const profileKey = selectedProfile ? selectedProfile.toUpperCase() : 'BLIND';
  const profileRep = result.representations?.[profileKey] || result.representations?.[profileKey.toLowerCase()] || {};

  const mainParagraph = profileRep.primary_text || result.extracted_text || result.summary || 'No extracted document text available.';
  const sectionTitle = profileRep.secondary_text || result.alt_text || 'Document Layout Overview';
  const summaryText = result.summary || profileRep.summary || 'Summary unavailable.';
  const keyConceptText = result.key_terms && result.key_terms.length > 0
    ? `Key Terms: ${result.key_terms.join(', ')}`
    : summaryText;

  return {
    id: `doc-lesson-${result.document_id || Date.now()}`,
    title: file.name,
    subject: `Member 1 Vision & Member 3 NLP AI`,
    lessonNumber: 1,
    totalLessons: 1,
    content: {
      heading: `Document Analysis: ${file.name}`,
      sectionHeading: sectionTitle,
      paragraph: mainParagraph,
      keyConceptTitle: 'AI Multi-Profile Summary & Key Concepts',
      keyConceptText: keyConceptText,
    },
    audio: {
      title: `Narration: ${file.name}`,
      duration: 60,
      formattedDuration: '01:00',
    },
    transcript: [
      {
        id: `doc-seg-0`,
        startTime: 0,
        timestamp: '00:00',
        text: mainParagraph,
      }
    ],
    captions: [
      {
        id: `doc-cap-0`,
        startTime: 0,
        endTime: 60,
        text: mainParagraph,
      }
    ],
  };
}
