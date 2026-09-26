import { useState, useEffect } from 'react';
import { SkipToContent } from './components/SkipToContent';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { LandingPage } from './pages/LandingPage';
import { ProfileSelectionPage } from './pages/ProfileSelectionPage';
import { LessonWorkspacePage } from './pages/LessonWorkspacePage';
import { UploadPage } from './pages/UploadPage';
import { NotificationBanner } from './components/NotificationBanner';
import { type ProfileId, PROFILES_DATA } from './types/profile';
import { type LessonData } from './types/lesson';

export function App() {
  const [activeTab, setActiveTab] = useState<'landing' | 'select-profile' | 'workspace' | 'upload'>('landing');
  const [selectedProfile, setSelectedProfile] = useState<ProfileId | null>(null);
  
  // Store raw File object
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Store real processed LessonData from Member 2 API pipeline
  const [processedLessonData, setProcessedLessonData] = useState<LessonData | null>(null);

  const [notification, setNotification] = useState<string | null>(null);

  const [isHighContrast, setIsHighContrast] = useState<boolean>(false);
  const [isDyslexiaFont, setIsDyslexiaFont] = useState<boolean>(false);

  // Sync high contrast & dyslexia class toggles on body element
  useEffect(() => {
    if (isHighContrast) {
      document.body.classList.add('high-contrast-mode');
    } else {
      document.body.classList.remove('high-contrast-mode');
    }
  }, [isHighContrast]);

  useEffect(() => {
    if (isDyslexiaFont) {
      document.body.classList.add('dyslexia-font-mode');
    } else {
      document.body.classList.remove('dyslexia-font-mode');
    }
  }, [isDyslexiaFont]);

  const handleShowNotification = (message: string) => {
    setNotification(message);
    setTimeout(() => {
      setNotification((prev) => (prev === message ? null : prev));
    }, 6000);
  };

  const handleSelectProfile = (profileId: ProfileId) => {
    setSelectedProfile(profileId);
    const profileObj = PROFILES_DATA.find((p) => p.id === profileId);
    if (profileObj) {
      handleShowNotification(`Selected ${profileObj.name} Profile (${profileObj.badgeText}). Click Continue to enter Lesson Workspace.`);
    }
  };

  const handleSelectProfileFromLanding = (profileId: ProfileId) => {
    handleSelectProfile(profileId);
    setActiveTab('select-profile');
    window.scrollTo(0, 0);
  };

  const handleContinueToWorkspace = () => {
    if (selectedProfile) {
      setActiveTab('workspace');
      window.scrollTo(0, 0);
    }
  };

  const handleOpenUpload = () => {
    setActiveTab('upload');
    window.scrollTo(0, 0);
  };

  return (
    <>
      <SkipToContent />

      <Header
        activeTab={activeTab}
        onNavigate={(tab) => {
          setActiveTab(tab);
          window.scrollTo(0, 0);
        }}
        onOpenUpload={handleOpenUpload}
        selectedProfile={selectedProfile}
        isHighContrast={isHighContrast}
        onToggleHighContrast={() => setIsHighContrast(!isHighContrast)}
        isDyslexiaFont={isDyslexiaFont}
        onToggleDyslexiaFont={() => setIsDyslexiaFont(!isDyslexiaFont)}
      />

      <main id="main-content" tabIndex={-1}>
        {activeTab === 'landing' && (
          <LandingPage
            onStartLearning={() => {
              setActiveTab('select-profile');
              window.scrollTo(0, 0);
            }}
            onOpenUpload={handleOpenUpload}
            onSelectProfile={handleSelectProfileFromLanding}
          />
        )}

        {activeTab === 'select-profile' && (
          <ProfileSelectionPage
            selectedProfile={selectedProfile}
            onSelectProfile={handleSelectProfile}
            onContinue={handleContinueToWorkspace}
            onBackToLanding={() => {
              setActiveTab('landing');
              window.scrollTo(0, 0);
            }}
          />
        )}

        {activeTab === 'workspace' && (
          <LessonWorkspacePage
            selectedProfile={selectedProfile}
            processedLessonData={processedLessonData}
            onChangeProfile={() => {
              setActiveTab('select-profile');
              window.scrollTo(0, 0);
            }}
            onBackToLanding={() => {
              setActiveTab('landing');
              window.scrollTo(0, 0);
            }}
            onOpenUpload={handleOpenUpload}
            onShowNotification={handleShowNotification}
          />
        )}

        {activeTab === 'upload' && (
          <UploadPage
            selectedFile={selectedFile}
            onFileChange={(file) => setSelectedFile(file)}
            selectedProfile={selectedProfile}
            onChangeProfile={() => {
              setActiveTab('select-profile');
              window.scrollTo(0, 0);
            }}
            onBackToLanding={() => {
              setActiveTab('landing');
              window.scrollTo(0, 0);
            }}
            onNavigateToWorkspace={() => {
              setActiveTab('workspace');
              window.scrollTo(0, 0);
            }}
            onShowNotification={handleShowNotification}
            onProcessSuccess={(data) => setProcessedLessonData(data)}
          />
        )}
      </main>

      <Footer
        onNavigate={(tab) => {
          setActiveTab(tab);
          window.scrollTo(0, 0);
        }}
        onOpenUpload={handleOpenUpload}
      />

      <NotificationBanner
        message={notification}
        onClear={() => setNotification(null)}
      />
    </>
  );
}

export default App;
