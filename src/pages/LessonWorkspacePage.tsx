import React, { useState } from 'react';
import { type ProfileId, getProfileModeConfig } from '../types/profile';
import { SAMPLE_LESSON_DATA, type LessonData } from '../types/lesson';
import { ProfileModeBanner } from '../components/ProfileModeBanner';
import { AudioPlayer } from '../components/AudioPlayer';
import { TranscriptPanel } from '../components/TranscriptPanel';
import { CaptionPanel } from '../components/CaptionPanel';
import { LessonNavigation } from '../components/LessonNavigation';

interface LessonWorkspacePageProps {
  selectedProfile: ProfileId | null;
  processedLessonData?: LessonData | null;
  onChangeProfile: () => void;
  onBackToLanding: () => void;
  onOpenUpload: () => void;
  onShowNotification: (message: string) => void;
}

export const LessonWorkspacePage: React.FC<LessonWorkspacePageProps> = ({
  selectedProfile,
  processedLessonData,
  onChangeProfile,
  onBackToLanding,
  onOpenUpload,
  onShowNotification,
}) => {
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [currentLessonNum, setCurrentLessonNum] = useState<number>(1);

  const activeLessonData = processedLessonData || SAMPLE_LESSON_DATA;
  const modeConfig = getProfileModeConfig(selectedProfile);

  const handlePrevLesson = () => {
    if (currentLessonNum > 1) {
      setCurrentLessonNum(currentLessonNum - 1);
      setCurrentTime(0);
      onShowNotification(`Loaded Lesson ${currentLessonNum - 1} of ${activeLessonData.totalLessons}.`);
    }
  };

  const handleNextLesson = () => {
    if (currentLessonNum < activeLessonData.totalLessons) {
      setCurrentLessonNum(currentLessonNum + 1);
      setCurrentTime(0);
      onShowNotification(`Loaded Lesson ${currentLessonNum + 1} of ${activeLessonData.totalLessons}.`);
    }
  };

  return (
    <div className={`workspace-page container ${modeConfig.containerClass}`}>
      {/* Workspace Navigation Bar */}
      <div className="workspace-header-bar">
        <div className="header-left">
          <button
            type="button"
            className="btn-secondary"
            onClick={onBackToLanding}
            aria-label="Return to landing home view"
          >
            ← Home
          </button>
          <h1 style={{ fontSize: 'clamp(1.5rem, 3.5vw, 2.2rem)', margin: 0 }}>
            Lesson Workspace
          </h1>
        </div>
      </div>

      {/* Reusable Profile Mode Banner */}
      <ProfileModeBanner
        selectedProfile={selectedProfile}
        onChangeProfile={onChangeProfile}
      />

      {/* 2. MAIN WORKSPACE CONTENT GRID (LAYOUT RE-ORDERED BASED ON ACTIVE PROFILE) */}
      <div className="workspace-main-layout">
        {/* BLIND MODE: Audio player is prioritized at the top of the primary column */}
        {selectedProfile === 'BLIND' && (
          <>
            <div className="workspace-primary-col">
              {/* Prioritized Audio Player for Blind profile */}
              <AudioPlayer
                lessonData={activeLessonData}
                currentTime={currentTime}
                onSeek={(newTime) => setCurrentTime(newTime)}
                onShowNotification={onShowNotification}
              />

              {/* Lesson Text Content */}
              <article className="lesson-content-card" aria-labelledby="lesson-title-heading">
                <header className="content-meta">
                  <span className="lesson-tag">{activeLessonData.subject}</span>
                  <span className="a11y-badge">{modeConfig.modeTitle} Active</span>
                </header>

                <h2 id="lesson-title-heading" className="lesson-main-heading">
                  {activeLessonData.content.heading}
                </h2>

                <h3 className="lesson-section-heading">
                  {activeLessonData.content.sectionHeading}
                </h3>

                <p className="lesson-body-paragraph">
                  {activeLessonData.content.paragraph}
                </p>

                <aside className="key-concept-box" aria-labelledby="concept-callout-title">
                  <div className="concept-box-header">
                    <span className="concept-icon" aria-hidden="true">💡</span>
                    <h4 id="concept-callout-title" className="concept-title">
                      {activeLessonData.content.keyConceptTitle}
                    </h4>
                  </div>
                  <p className="concept-text">
                    {activeLessonData.content.keyConceptText}
                  </p>
                </aside>
              </article>

              <LessonNavigation
                currentLessonNumber={currentLessonNum}
                totalLessons={activeLessonData.totalLessons}
                onPreviousLesson={handlePrevLesson}
                onNextLesson={handleNextLesson}
              />
            </div>

            <div className="workspace-secondary-col">
              <TranscriptPanel
                segments={activeLessonData.transcript}
                currentTime={currentTime}
                onSeekToSegment={(startTime) => setCurrentTime(startTime)}
              />

              <CaptionPanel
                captions={activeLessonData.captions}
                currentTime={currentTime}
              />
            </div>
          </>
        )}

        {/* DEAF MODE: Captions & Transcript are prioritized at the top */}
        {selectedProfile === 'DEAF' && (
          <>
            <div className="workspace-primary-col">
              {/* Prioritized Captions & Transcript for Deaf profile */}
              <CaptionPanel
                captions={activeLessonData.captions}
                currentTime={currentTime}
              />

              <TranscriptPanel
                segments={activeLessonData.transcript}
                currentTime={currentTime}
                onSeekToSegment={(startTime) => setCurrentTime(startTime)}
              />

              <article className="lesson-content-card" aria-labelledby="lesson-title-heading">
                <header className="content-meta">
                  <span className="lesson-tag">{activeLessonData.subject}</span>
                  <span className="a11y-badge">{modeConfig.modeTitle} Active</span>
                </header>

                <h2 id="lesson-title-heading" className="lesson-main-heading">
                  {activeLessonData.content.heading}
                </h2>

                <h3 className="lesson-section-heading">
                  {activeLessonData.content.sectionHeading}
                </h3>

                <p className="lesson-body-paragraph">
                  {activeLessonData.content.paragraph}
                </p>

                <aside className="key-concept-box" aria-labelledby="concept-callout-title">
                  <div className="concept-box-header">
                    <span className="concept-icon" aria-hidden="true">💡</span>
                    <h4 id="concept-callout-title" className="concept-title">
                      {activeLessonData.content.keyConceptTitle}
                    </h4>
                  </div>
                  <p className="concept-text">
                    {activeLessonData.content.keyConceptText}
                  </p>
                </aside>
              </article>

              <LessonNavigation
                currentLessonNumber={currentLessonNum}
                totalLessons={activeLessonData.totalLessons}
                onPreviousLesson={handlePrevLesson}
                onNextLesson={handleNextLesson}
              />
            </div>

            <div className="workspace-secondary-col">
              {/* Secondary Audio Controls */}
              <AudioPlayer
                lessonData={activeLessonData}
                currentTime={currentTime}
                onSeek={(newTime) => setCurrentTime(newTime)}
                onShowNotification={onShowNotification}
              />

              <div className="upload-shortcut-box">
                <h3 style={{ fontSize: '1.05rem', marginBottom: '0.4rem' }}>
                  Want to learn from custom files?
                </h3>
                <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--color-text-muted)' }}>
                  Upload your own textbooks, PDFs, or audio lectures.
                </p>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ width: '100%' }}
                  onClick={onOpenUpload}
                >
                  Upload Content
                </button>
              </div>
            </div>
          </>
        )}

        {/* DEFAULT, LOW_VISION, & DYSLEXIA MODES */}
        {selectedProfile !== 'BLIND' && selectedProfile !== 'DEAF' && (
          <>
            <div className="workspace-primary-col">
              <article className="lesson-content-card" aria-labelledby="lesson-title-heading">
                <header className="content-meta">
                  <span className="lesson-tag">{activeLessonData.subject}</span>
                  <span className="a11y-badge">{modeConfig.modeTitle} Active</span>
                </header>

                <h2 id="lesson-title-heading" className="lesson-main-heading">
                  {activeLessonData.content.heading}
                </h2>

                <h3 className="lesson-section-heading">
                  {activeLessonData.content.sectionHeading}
                </h3>

                <p className="lesson-body-paragraph">
                  {activeLessonData.content.paragraph}
                </p>

                <aside className="key-concept-box" aria-labelledby="concept-callout-title">
                  <div className="concept-box-header">
                    <span className="concept-icon" aria-hidden="true">💡</span>
                    <h4 id="concept-callout-title" className="concept-title">
                      {activeLessonData.content.keyConceptTitle}
                    </h4>
                  </div>
                  <p className="concept-text">
                    {activeLessonData.content.keyConceptText}
                  </p>
                </aside>
              </article>

              <AudioPlayer
                lessonData={activeLessonData}
                currentTime={currentTime}
                onSeek={(newTime) => setCurrentTime(newTime)}
                onShowNotification={onShowNotification}
              />

              <LessonNavigation
                currentLessonNumber={currentLessonNum}
                totalLessons={activeLessonData.totalLessons}
                onPreviousLesson={handlePrevLesson}
                onNextLesson={handleNextLesson}
              />
            </div>

            <div className="workspace-secondary-col">
              <CaptionPanel
                captions={activeLessonData.captions}
                currentTime={currentTime}
              />

              <TranscriptPanel
                segments={activeLessonData.transcript}
                currentTime={currentTime}
                onSeekToSegment={(startTime) => setCurrentTime(startTime)}
              />

              <div className="upload-shortcut-box">
                <h3 style={{ fontSize: '1.05rem', marginBottom: '0.4rem' }}>
                  Want to learn from custom files?
                </h3>
                <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--color-text-muted)' }}>
                  Upload your own textbooks, PDFs, or audio lectures.
                </p>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ width: '100%' }}
                  onClick={onOpenUpload}
                >
                  Upload Content
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
