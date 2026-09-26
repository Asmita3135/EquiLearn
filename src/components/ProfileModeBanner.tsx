import React from 'react';
import { type ProfileId, getProfileModeConfig } from '../types/profile';

interface ProfileModeBannerProps {
  selectedProfile: ProfileId | null;
  onChangeProfile: () => void;
}

export const ProfileModeBanner: React.FC<ProfileModeBannerProps> = ({
  selectedProfile,
  onChangeProfile,
}) => {
  const config = getProfileModeConfig(selectedProfile);

  return (
    <div
      className={`profile-mode-banner ${config.containerClass}`}
      role="region"
      aria-label="Active Accessibility Profile Mode"
    >
      <div className="banner-info-group">
        <div className="banner-icon-badge" aria-hidden="true">
          {config.iconSymbol}
        </div>

        <div className="banner-text-details">
          <div className="banner-profile-tag">
            <span className="a11y-badge">{config.profileName}</span>
          </div>

          <h2 className="banner-mode-title" style={{ fontSize: '1.25rem', margin: '0.2rem 0' }}>
            {config.modeTitle}
          </h2>

          <p className="banner-explanation" style={{ margin: 0, fontSize: '0.925rem' }}>
            {config.explanation}
          </p>
        </div>
      </div>

      <button
        type="button"
        className="btn-secondary banner-change-btn"
        onClick={onChangeProfile}
        aria-label={`Change current profile mode from ${config.profileName}`}
      >
        Change Profile
      </button>
    </div>
  );
};
