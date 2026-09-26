import React from 'react';
import { type TranscriptSegment } from '../types/lesson';

interface TranscriptPanelProps {
  segments: TranscriptSegment[];
  currentTime: number;
  onSeekToSegment: (startTime: number) => void;
}

export const TranscriptPanel: React.FC<TranscriptPanelProps> = ({
  segments,
  currentTime,
  onSeekToSegment,
}) => {
  return (
    <section className="transcript-panel-card" aria-labelledby="transcript-heading">
      <div className="panel-header">
        <h2 id="transcript-heading" style={{ fontSize: '1.25rem', margin: 0 }}>
          Transcript
        </h2>
        <span className="a11y-badge">Synchronized Text</span>
      </div>

      <p style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)', marginBottom: '1.25rem' }}>
        Select any timestamp below to jump directly to that point in the lesson audio.
      </p>

      <ol className="transcript-segments-list" aria-label="Lesson audio transcript segments">
        {segments.map((seg, idx) => {
          // Check if current time falls within this segment
          const nextSeg = segments[idx + 1];
          const isCurrentSegment =
            currentTime >= seg.startTime && (!nextSeg || currentTime < nextSeg.startTime);

          return (
            <li
              key={seg.id}
              className={`transcript-segment-item ${isCurrentSegment ? 'active-segment' : ''}`}
            >
              <button
                type="button"
                className="timestamp-btn"
                onClick={() => onSeekToSegment(seg.startTime)}
                aria-label={`Jump audio to timestamp ${seg.timestamp}`}
                title={`Seek to ${seg.timestamp}`}
              >
                [{seg.timestamp}]
              </button>

              <span className="segment-text">
                {isCurrentSegment && (
                  <span className="active-indicator-badge" aria-hidden="true">
                    ▶ Active
                  </span>
                )}
                {seg.text}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
};
