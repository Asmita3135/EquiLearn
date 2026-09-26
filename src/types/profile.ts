export type ProfileId = 'BLIND' | 'LOW_VISION' | 'DEAF' | 'DYSLEXIA';

export interface ProfileOption {
  id: ProfileId;
  name: string;
  badgeText: string;
  description: string;
  iconSymbol: string;
  bulletPoints: string[];
}

export interface ProfileModeConfig {
  id: ProfileId | 'DEFAULT';
  profileName: string;
  modeTitle: string;
  explanation: string;
  iconSymbol: string;
  containerClass: string;
}

export const PROFILES_DATA: ProfileOption[] = [
  {
    id: 'BLIND',
    name: 'Blind',
    badgeText: 'Audio-First Learning',
    description: 'Designed for learners who rely on audio-first content, screen readers, and spoken descriptions.',
    iconSymbol: '🔊',
    bulletPoints: [
      'Audio-first learning',
      'Screen-reader-friendly content',
      'Read-aloud/audio learning'
    ]
  },
  {
    id: 'LOW_VISION',
    name: 'Low Vision',
    badgeText: 'Enhanced Visual Presentation',
    description: 'Tailored for learners needing scalable high-contrast layouts, large fonts, and clear legibility.',
    iconSymbol: '👁️',
    bulletPoints: [
      'Enhanced visual presentation',
      'High contrast',
      'Larger/readable content'
    ]
  },
  {
    id: 'DEAF',
    name: 'Deaf / Hard of Hearing',
    badgeText: 'Captions & Transcripts',
    description: 'Optimized for visual learners with comprehensive closed captions, synchronized transcripts, and visual cues.',
    iconSymbol: '💬',
    bulletPoints: [
      'Captions',
      'Transcripts',
      'Visual learning cues'
    ]
  },
  {
    id: 'DYSLEXIA',
    name: 'Dyslexia',
    badgeText: 'Comfortable Reading Experience',
    description: 'Crafted for learners who benefit from specialized typography, comfortable line spacing, and structured content.',
    iconSymbol: '📖',
    bulletPoints: [
      'Simplified content',
      'Readable typography',
      'Comfortable spacing',
      'Focused reading experience'
    ]
  }
];

export function getProfileModeConfig(id: ProfileId | null): ProfileModeConfig {
  switch (id) {
    case 'BLIND':
      return {
        id: 'BLIND',
        profileName: 'Blind Profile',
        modeTitle: 'Audio-first learning mode',
        explanation: 'This lesson is optimized for audio-first learning.',
        iconSymbol: '🔊',
        containerClass: 'mode-blind-audio'
      };
    case 'LOW_VISION':
      return {
        id: 'LOW_VISION',
        profileName: 'Low Vision Profile',
        modeTitle: 'Enhanced visual learning mode',
        explanation: 'This lesson is optimized with enlarged text, high contrast, and enhanced section spacing.',
        iconSymbol: '👁️',
        containerClass: 'mode-low-vision'
      };
    case 'DEAF':
      return {
        id: 'DEAF',
        profileName: 'Deaf / Hard of Hearing Profile',
        modeTitle: 'Caption and transcript mode',
        explanation: 'This lesson is optimized with primary visual captions and interactive transcript text.',
        iconSymbol: '💬',
        containerClass: 'mode-deaf-captions'
      };
    case 'DYSLEXIA':
      return {
        id: 'DYSLEXIA',
        profileName: 'Dyslexia Profile',
        modeTitle: 'Readable learning mode',
        explanation: 'This lesson is optimized with relaxed line spacing, dyslexia-friendly typography, and scannable text chunks.',
        iconSymbol: '📖',
        containerClass: 'mode-dyslexia-readable'
      };
    default:
      return {
        id: 'DEFAULT',
        profileName: 'Standard Profile',
        modeTitle: 'Standard learning mode',
        explanation: 'Standard multi-sensory educational view.',
        iconSymbol: '⚙️',
        containerClass: 'mode-standard'
      };
  }
}
