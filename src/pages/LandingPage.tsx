import React from 'react';
import { AccessibilityProfilesSection } from '../components/AccessibilityProfilesSection';
import { type ProfileId } from '../types/profile';

interface LandingPageProps {
  onStartLearning: () => void;
  onOpenUpload: () => void;
  onSelectProfile: (profileId: ProfileId) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onStartLearning,
  onOpenUpload,
  onSelectProfile,
}) => {
  return (
    <div>
      {/* Hero Section */}
      <section className="hero-section" aria-labelledby="hero-heading">
        <div className="container">
          <div className="hero-content">
            <span className="section-tag" style={{ marginBottom: '1rem' }}>
              Inclusive Education Platform
            </span>

            <h1 id="hero-heading">Learn Without Limits</h1>

            <p className="hero-description">
              EquiLearn breaks down learning barriers by adapting course content into multi-sensory experiences tailored specifically for Blind, Low Vision, Deaf/Hard of Hearing, and Dyslexic learners.
            </p>

            <div className="hero-actions">
              <button
                type="button"
                className="btn-primary"
                onClick={onStartLearning}
              >
                Choose Learning Profile & Start
              </button>
              
              <button
                type="button"
                className="btn-secondary"
                onClick={onOpenUpload}
              >
                Upload Content
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Accessibility Learning Profiles Section */}
      <AccessibilityProfilesSection onSelectProfile={onSelectProfile} />

      {/* Core Principles & Standards Highlight */}
      <section className="features-section" aria-labelledby="features-heading">
        <div className="container">
          <div className="section-header">
            <h2 id="features-heading">Built for Universal Accessibility</h2>
            <p>Designed from the ground up to support accessible digital learning standards.</p>
          </div>

          <div className="features-grid">
            <article className="feature-box">
              <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Screen Reader First</h3>
              <p style={{ fontSize: '0.95rem', margin: 0 }}>
                Structured semantic HTML, intuitive ARIA landmarks, and unhindered keyboard flow ensure seamless navigation with NVDA, JAWS, and VoiceOver.
              </p>
            </article>

            <article className="feature-box">
              <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>High Contrast & Scaling</h3>
              <p style={{ fontSize: '0.95rem', margin: 0 }}>
                Built-in high-contrast color tokens and flexible CSS geometry ensure crisp legibility up to 200%+ browser zoom without horizontal scrolling.
              </p>
            </article>

            <article className="feature-box">
              <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>Multi-Sensory Options</h3>
              <p style={{ fontSize: '0.95rem', margin: 0 }}>
                Seamless integration paths for text-to-speech audio, synchronized captions, visual highlights, and specialized typography.
              </p>
            </article>
          </div>
        </div>
      </section>
    </div>
  );
};
