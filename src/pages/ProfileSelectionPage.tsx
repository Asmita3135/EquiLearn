import React from 'react';
import { AccessibilityProfileSelector } from '../components/AccessibilityProfileSelector';
import { type ProfileId } from '../types/profile';

interface ProfileSelectionPageProps {
  selectedProfile: ProfileId | null;
  onSelectProfile: (profileId: ProfileId) => void;
  onContinue: () => void;
  onBackToLanding: () => void;
}

export const ProfileSelectionPage: React.FC<ProfileSelectionPageProps> = ({
  selectedProfile,
  onSelectProfile,
  onContinue,
  onBackToLanding,
}) => {
  return (
    <div className="profile-selection-page" style={{ padding: '2.5rem 0 4rem' }}>
      <AccessibilityProfileSelector
        selectedProfile={selectedProfile}
        onSelectProfile={onSelectProfile}
        onContinue={onContinue}
        onBack={onBackToLanding}
      />
    </div>
  );
};
