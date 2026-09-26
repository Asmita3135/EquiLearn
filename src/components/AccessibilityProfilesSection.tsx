import React from 'react';
import { type ProfileId, PROFILES_DATA } from '../types/profile';

interface AccessibilityProfilesSectionProps {
  onSelectProfile: (profileId: ProfileId) => void;
}

export const AccessibilityProfilesSection: React.FC<AccessibilityProfilesSectionProps> = ({
  onSelectProfile
}) => {
  return (
    <section className="profiles-section" aria-labelledby="profiles-heading">
      <div className="container">
        <div className="section-header">
          <span className="section-tag">Universal Design for Learning</span>
          <h2 id="profiles-heading">Accessibility Learning Profiles</h2>
          <p>
            EquiLearn adapts lesson content dynamically to fit each student's unique sensory and cognitive preferences.
          </p>
        </div>

        <div className="profiles-grid">
          {PROFILES_DATA.map((profile) => (
            <article key={profile.id} className="profile-card">
              <div className="profile-icon-wrapper" aria-hidden="true">
                <span style={{ fontSize: '1.5rem' }}>{profile.iconSymbol}</span>
              </div>
              
              <div className="profile-title">
                <h3>{profile.name}</h3>
              </div>

              <span className="a11y-badge" style={{ alignSelf: 'flex-start', margin: '0.25rem 0 0.75rem' }}>
                {profile.badgeText}
              </span>

              <p style={{ fontSize: '0.95rem' }}>{profile.description}</p>

              <ul className="profile-features-list" aria-label={`Key features for ${profile.name}`}>
                {profile.bulletPoints.map((feature, idx) => (
                  <li key={idx} className="profile-feature-item">
                    <span className="bullet-icon" aria-hidden="true">✓</span>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                type="button"
                className="btn-secondary"
                style={{ width: '100%' }}
                onClick={() => onSelectProfile(profile.id)}
              >
                Select {profile.name} Profile
              </button>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
};
