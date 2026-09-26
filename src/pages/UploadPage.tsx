import React from 'react';
import { FileUpload } from '../components/FileUpload';
import { type ProfileId } from '../types/profile';
import { type LessonData } from '../types/lesson';

interface UploadPageProps {
  selectedFile: File | null;
  onFileChange: (file: File | null) => void;
  selectedProfile: ProfileId | null;
  onChangeProfile: () => void;
  onBackToLanding: () => void;
  onNavigateToWorkspace: () => void;
  onShowNotification: (message: string) => void;
  onProcessSuccess: (lessonData: LessonData) => void;
}

export const UploadPage: React.FC<UploadPageProps> = ({
  selectedFile,
  onFileChange,
  selectedProfile,
  onChangeProfile,
  onBackToLanding,
  onNavigateToWorkspace,
  onShowNotification,
  onProcessSuccess,
}) => {
  return (
    <div className="upload-page container" style={{ padding: '2.5rem 0 4rem' }}>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <span className="section-tag">Content Adaptation Engine</span>
          <h1 style={{ fontSize: 'clamp(1.75rem, 4vw, 2.5rem)', marginTop: '0.4rem', marginBottom: '0.5rem' }}>
            Upload Learning Content
          </h1>
          <p style={{ margin: 0, maxWidth: '65ch', color: 'var(--color-text-muted)' }}>
            Upload textbooks, lecture audio, educational videos, or study notes. EquiLearn will adapt them into accessible multi-sensory formats.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button type="button" className="btn-secondary" onClick={onBackToLanding}>
            ← Back to Home
          </button>
          <button type="button" className="btn-primary" onClick={onNavigateToWorkspace}>
            Lesson Workspace →
          </button>
        </div>
      </div>

      <FileUpload
        selectedFile={selectedFile}
        onFileChange={onFileChange}
        selectedProfile={selectedProfile}
        onChangeProfile={onChangeProfile}
        onShowNotification={onShowNotification}
        onNavigateToWorkspace={onNavigateToWorkspace}
        onProcessSuccess={onProcessSuccess}
      />
    </div>
  );
};
