import React from 'react';
import { type CaptionItem } from '../types/lesson';

interface CaptionPanelProps {
  captions: CaptionItem[];
  currentTime: number;
}

export const CaptionPanel: React.FC<CaptionPanelProps> = ({ captions, currentTime }) => {
  // Find current caption segment matching currentTime
  const activeCaption = captions.find(
    (c) => currentTime >= c.startTime && currentTime <= c.endTime
  ) || captions[0]; // fallback to first caption as sample display

  return (
    <section className="caption-panel-card" aria-labelledby="captions-heading">
      <div className="panel-header">
        <h2 id="captions-heading" style={{ fontSize: '1.25rem', margin: 0 }}>
          Captions
        </h2>
        <span className="a11y-badge">Visual Subtitles</span>
      </div>

      <div className="caption-display-box" aria-live="polite" role="region" aria-label="Live lesson caption stream">
        <div className="caption-text-content">
          "{activeCaption ? activeCaption.text : 'Welcome to this lesson on accessible learning.'}"
        </div>
      </div>

      <div className="caption-notice-footer">
        <span aria-hidden="true">ℹ️</span>
        <span>
          Note: This is sample/placeholder caption content. Synchronized VTT/SRT caption streams will be connected when Member 2 AI processing services are integrated.
        </span>
      </div>
    </section>
  );
};
