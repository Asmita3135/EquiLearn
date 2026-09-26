export interface TranscriptSegment {
  id: string;
  startTime: number; // in seconds
  timestamp: string; // e.g. "00:08"
  text: string;
  speaker?: string;
}

export interface CaptionItem {
  id: string;
  startTime: number;
  endTime: number;
  text: string;
}

export interface LessonData {
  id: string;
  title: string;
  subject: string;
  lessonNumber: number;
  totalLessons: number;
  content: {
    heading: string;
    sectionHeading: string;
    paragraph: string;
    keyConceptTitle: string;
    keyConceptText: string;
  };
  audio: {
    title: string;
    duration: number; // in seconds (e.g. 105 seconds = 1:45)
    formattedDuration: string;
    src?: string;
  };
  transcript: TranscriptSegment[];
  captions: CaptionItem[];
}

export const SAMPLE_LESSON_DATA: LessonData = {
  id: 'lesson-101',
  title: 'Introduction to Accessible Learning',
  subject: 'Universal Design for Learning',
  lessonNumber: 1,
  totalLessons: 5,
  content: {
    heading: 'Introduction to Accessible Learning',
    sectionHeading: 'Understanding Sensory & Cognitive Profiles',
    paragraph: 'Accessible digital education ensures that every student, regardless of vision, hearing, or reading differences, can engage fully with educational materials. By decoupling learning content from a single fixed visual or auditory format, content can be dynamically transformed to match the learner\'s preferred profile.',
    keyConceptTitle: 'Key Concept: Multi-Sensory Content Equivalence',
    keyConceptText: 'Providing information through multiple representation modes (such as audio-first narration, synchronized captions, and dyslexia-friendly text chunking) guarantees that no learner is left behind due to sensory or cognitive barriers.'
  },
  audio: {
    title: 'Lesson 1 Audio Narration',
    duration: 105,
    formattedDuration: '01:45'
  },
  transcript: [
    {
      id: 't-1',
      startTime: 0,
      timestamp: '00:00',
      text: 'Welcome to this lesson on accessible learning.'
    },
    {
      id: 't-2',
      startTime: 8,
      timestamp: '00:08',
      text: 'In this lesson, we will explore how digital learning materials can be adapted for different accessibility needs.'
    },
    {
      id: 't-3',
      startTime: 20,
      timestamp: '00:20',
      text: 'Accessibility profiles help learners receive information in a format that works for them.'
    },
    {
      id: 't-4',
      startTime: 42,
      timestamp: '00:42',
      text: 'By combining screen-reader navigation, clear captions, and dyslexia-friendly typography, we achieve universal design.'
    },
    {
      id: 't-5',
      startTime: 75,
      timestamp: '01:15',
      text: 'Thank you for exploring EquiLearn. Proceed to the next section to continue your learning journey.'
    }
  ],
  captions: [
    {
      id: 'c-1',
      startTime: 0,
      endTime: 7,
      text: 'Welcome to this lesson on accessible learning.'
    },
    {
      id: 'c-2',
      startTime: 8,
      endTime: 19,
      text: 'In this lesson, we will explore how digital learning materials can be adapted for different accessibility needs.'
    },
    {
      id: 'c-3',
      startTime: 20,
      endTime: 41,
      text: 'Accessibility profiles help learners receive information in a format that works for them.'
    }
  ]
};
