import React, { useState } from 'react';
import { FileDropZone } from './FileDropZone';
import { FileSummary } from './FileSummary';
import { validateFile, type UploadStatus, type FileValidationResult } from '../types/upload';
import { type ProfileId, PROFILES_DATA } from '../types/profile';
import { processAudioSpeechApi, convertMember2ResultToLessonData } from '../services/audioSpeech';
import { processDocumentApi, convertDocumentResultToLessonData } from '../services/documentService';
import { type LessonData } from '../types/lesson';

interface FileUploadProps {
  selectedFile: File | null;
  onFileChange: (file: File | null) => void;
  selectedProfile: ProfileId | null;
  onChangeProfile: () => void;
  onShowNotification: (message: string) => void;
  onNavigateToWorkspace: () => void;
  onProcessSuccess: (lessonData: LessonData) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  selectedFile,
  onFileChange,
  selectedProfile,
  onChangeProfile,
  onShowNotification,
  onNavigateToWorkspace,
  onProcessSuccess,
}) => {
  const [status, setStatus] = useState<UploadStatus>(selectedFile ? 'READY' : 'IDLE');
  const [validation, setValidation] = useState<FileValidationResult | null>(
    selectedFile ? validateFile(selectedFile) : null
  );
  const [apiError, setApiError] = useState<string | null>(null);

  const activeProfileObj = PROFILES_DATA.find((p) => p.id === selectedProfile);

  const handleSelectFile = (file: File) => {
    onFileChange(file);
    setApiError(null);
    const result = validateFile(file);
    setValidation(result);

    if (result.isValid) {
      setStatus('READY');
      onShowNotification(`Selected file "${file.name}" (${result.categoryLabel}). Ready to process.`);
    } else {
      setStatus('ERROR');
      onShowNotification(result.errorMessage || 'Invalid file format selected.');
    }
  };

  const handleClearFile = () => {
    onFileChange(null);
    setValidation(null);
    setApiError(null);
    setStatus('IDLE');
    onShowNotification('Cleared file selection.');
  };

  const handleProcessContent = async () => {
    if (!selectedFile || !validation?.isValid || status === 'PROCESSING') return;

    setStatus('PROCESSING');
    setApiError(null);

    const isDocument = ['pdf', 'image', 'text'].includes(validation.category);

    if (isDocument) {
      onShowNotification('Sending document to Member 1 Vision & Member 3 NLP pipeline...');
      try {
        const result = await processDocumentApi(selectedFile);
        const lessonData = convertDocumentResultToLessonData(selectedFile, result, selectedProfile);
        setStatus('COMPLETED_PLACEHOLDER');
        onProcessSuccess(lessonData);
        onShowNotification('Document processing complete! Loading Lesson Workspace...');
        onNavigateToWorkspace();
      } catch (err: unknown) {
        setStatus('ERROR');
        const msg = err instanceof Error ? err.message : 'Backend processing failed or server is offline.';
        setApiError(msg);
        onShowNotification(`Processing Error: ${msg}`);
      }
    } else {
      onShowNotification('Sending audio/video file to Member 2 FastAPI backend (Whisper & gTTS)...');
      try {
        const result = await processAudioSpeechApi(selectedFile);
        const lessonData = convertMember2ResultToLessonData(selectedFile, result);
        setStatus('COMPLETED_PLACEHOLDER');
        onProcessSuccess(lessonData);
        onShowNotification('Processing complete! Loading Lesson Workspace...');
        onNavigateToWorkspace();
      } catch (err: unknown) {
        setStatus('ERROR');
        const msg = err instanceof Error ? err.message : 'Backend processing failed or server is offline.';
        setApiError(msg);
        onShowNotification(`Processing Error: ${msg}`);
      }
    }
  };

  return (
    <section className="file-upload-experience" aria-labelledby="upload-experience-title">
      {/* Profile Awareness Banner */}
      <div className="upload-profile-banner" role="region" aria-label="Active Accessibility Profile">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '1.5rem' }} aria-hidden="true">
            {activeProfileObj ? activeProfileObj.iconSymbol : '⚙️'}
          </span>
          <div>
            <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--color-primary)' }}>
              Learning Profile
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--color-text-main)' }}>
              {activeProfileObj ? activeProfileObj.name : 'No Profile Selected (Default Mode)'}
            </div>
          </div>
        </div>

        <button
          type="button"
          className="btn-secondary"
          onClick={onChangeProfile}
          aria-label="Change current accessibility profile"
          style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
        >
          Change Profile
        </button>
      </div>

      <div className="upload-main-card">
        {!selectedFile || !validation ? (
          <FileDropZone onFileSelected={handleSelectFile} />
        ) : (
          <FileSummary
            file={selectedFile}
            validation={validation}
            status={status}
            onClearFile={handleClearFile}
          />
        )}

        {/* API Error Notification Banner */}
        {apiError && (
          <div
            role="alert"
            aria-live="polite"
            style={{
              padding: '0.85rem 1.1rem',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid var(--color-danger, #ef4444)',
              borderRadius: 'var(--radius-sm)',
              marginTop: '1rem',
              color: '#b91c1c',
              fontSize: '0.9rem',
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: '0.25rem' }}>⚠️ Backend API Error</div>
            <div>{apiError}</div>
            <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#7f1d1d' }}>
              Please make sure the EquiLearn FastAPI backend server is running at <code>http://localhost:8000</code>. Your selected file is ready to retry.
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div className="upload-actions-bar">
          {selectedFile && (
            <button
              type="button"
              className="btn-secondary"
              onClick={handleClearFile}
              disabled={status === 'PROCESSING'}
            >
              Select Different File
            </button>
          )}

          <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            {status === 'COMPLETED_PLACEHOLDER' ? (
              <button
                type="button"
                className="btn-primary"
                onClick={onNavigateToWorkspace}
              >
                Go to Lesson Workspace →
              </button>
            ) : (
              <button
                type="button"
                className="btn-primary"
                onClick={handleProcessContent}
                disabled={!selectedFile || !validation?.isValid || status === 'PROCESSING'}
                aria-disabled={!selectedFile || !validation?.isValid || status === 'PROCESSING'}
              >
                {status === 'PROCESSING' ? 'Processing with EquiLearn Backend...' : 'Process Content'}
              </button>
            )}
          </div>
        </div>

        {/* Integration Note */}
        <div className="integration-disclaimer-box" role="status" aria-live="polite">
          <span aria-hidden="true" style={{ fontSize: '1.1rem' }}>ℹ️</span>
          <span>
            <strong>EquiLearn FastAPI Backend Integration Active:</strong> Processing files via <code>http://localhost:8000</code>.
          </span>
        </div>
      </div>
    </section>
  );
};
