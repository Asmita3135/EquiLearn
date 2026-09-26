import React from 'react';
import { type ProfileId, PROFILES_DATA } from '../types/profile';

interface AccessibilityProfileSelectorProps {
  selectedProfile: ProfileId | null;
  onSelectProfile: (profileId: ProfileId) => void;
  onContinue: () => void;
  onBack?: () => void;
}

export const AccessibilityProfileSelector: React.FC<AccessibilityProfileSelectorProps> = ({
  selectedProfile,
  onSelectProfile,
  onContinue,
  onBack,
}) => {
  return (
    <section
      className="profile-selector-section"
      aria-labelledby="profile-selector-heading"
    >
      <div className="container">
        <div className="section-header" style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <span className="section-tag">Step 1 of 2</span>
          <h1 id="profile-selector-heading" style={{ fontSize: 'clamp(1.75rem, 4vw, 2.5rem)', marginTop: '0.5rem' }}>
            Choose Your Learning Profile
          </h1>
          <p style={{ margin: '0 auto', maxWidth: '65ch' }}>
            Select the accessibility profile that best matches your learning preferences. EquiLearn will tailor lesson formats, visuals, and sensory outputs for your needs.
          </p>
        </div>

        {/* Accessible Group Container */}
        <div
          role="group"
          aria-labelledby="profile-selector-heading"
          aria-describedby="profile-selector-instructions"
          className="profile-selector-grid-wrapper"
        >
          <span id="profile-selector-instructions" className="sr-only">
            Select one of the four accessibility learning profiles below using the Tab key and Enter or Space bar, then click Continue.
          </span>

          <div className="profile-selector-grid">
            {PROFILES_DATA.map((profile) => {
              const isSelected = selectedProfile === profile.id;

              return (
                <button
                  type="button"
                  key={profile.id}
                  className={`profile-select-card ${isSelected ? 'selected' : ''}`}
                  onClick={() => onSelectProfile(profile.id)}
                  aria-pressed={isSelected}
                  aria-label={`${profile.name} profile - ${isSelected ? 'Currently Selected' : 'Click to Select'}. ${profile.description}`}
                >
                  <div className="card-top-bar">
                    <div className="profile-icon" aria-hidden="true">
                      {profile.iconSymbol}
                    </div>

                    {/* Non-color reliant selection indicator */}
                    <div className={`selection-badge ${isSelected ? 'badge-selected' : 'badge-unselected'}`}>
                      {isSelected ? (
                        <>
                          <span className="badge-icon" aria-hidden="true">✓</span>
                          <span>Selected Profile</span>
                        </>
                      ) : (
                        <span>Select Profile</span>
                      )}
                    </div>
                  </div>

                  <h2 className="profile-card-title">{profile.name}</h2>
                  <p className="profile-card-desc">{profile.description}</p>

                  <ul className="profile-card-bullets" aria-label={`Key features for ${profile.name}`}>
                    {profile.bulletPoints.map((point, index) => (
                      <li key={index} className="bullet-item">
                        <span className="bullet-check" aria-hidden="true">✓</span>
                        <span>{point}</span>
                      </li>
                    ))}
                  </ul>
                </button>
              );
            })}
          </div>
        </div>

        {/* Actions Bar */}
        <div className="selector-actions-bar">
          {onBack && (
            <button
              type="button"
              className="btn-secondary"
              onClick={onBack}
            >
              ← Back
            </button>
          )}

          <div className="continue-wrapper" style={{ marginLeft: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem' }}>
            <button
              type="button"
              className="btn-primary continue-btn"
              disabled={!selectedProfile}
              aria-disabled={!selectedProfile}
              onClick={onContinue}
              style={{
                minWidth: '220px',
                opacity: selectedProfile ? 1 : 0.6,
                cursor: selectedProfile ? 'pointer' : 'not-allowed'
              }}
            >
              Continue to Lesson Workspace →
            </button>

            {!selectedProfile && (
              <span style={{ fontSize: '0.85rem', color: 'var(--color-text-light)', fontWeight: 600 }}>
                Please select a profile above to continue
              </span>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
