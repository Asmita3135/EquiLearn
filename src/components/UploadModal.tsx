import React, { useEffect, useRef } from 'react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onShowNotification: (message: string) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onShowNotification,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) {
      closeButtonRef.current?.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSimulatedSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onClose();
    onShowNotification(
      'Upload Placeholder: Content processing (OCR / Whisper / VLM) will be integrated when AI/ML backend services are connected.'
    );
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal-dialog"
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="upload-modal-title" style={{ fontSize: '1.4rem' }}>
            Upload Educational Content
          </h2>
          <button
            type="button"
            className="modal-close-btn"
            ref={closeButtonRef}
            onClick={onClose}
            aria-label="Close upload modal"
          >
            ✕ Close
          </button>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <span className="a11y-badge" style={{ marginBottom: '1rem' }}>
            Placeholder Feature (Frontend Only)
          </span>
          <p style={{ fontSize: '0.95rem', marginTop: '0.5rem' }}>
            Upload textbooks, PDFs, audio lectures, or educational videos. EquiLearn will process them into accessible formats for all learning profiles.
          </p>
        </div>

        <form onSubmit={handleSimulatedSubmit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label
              htmlFor="content-title-input"
              style={{ display: 'block', fontWeight: 600, marginBottom: '0.4rem' }}
            >
              Lesson / Book Title:
            </label>
            <input
              id="content-title-input"
              type="text"
              placeholder="e.g. Introductory Physics - Chapter 3"
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '6px',
                border: '1px solid var(--color-border)',
                fontSize: '1rem'
              }}
              required
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label
              htmlFor="file-upload-input"
              style={{ display: 'block', fontWeight: 600, marginBottom: '0.4rem' }}
            >
              Select File (PDF, MP3, MP4, TXT):
            </label>
            <input
              id="file-upload-input"
              type="file"
              accept=".pdf,.mp3,.mp4,.txt,.docx"
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px dashed var(--color-border-dark)',
                borderRadius: '6px',
                background: 'var(--color-bg)'
              }}
            />
            <small style={{ display: 'block', marginTop: '0.4rem', color: 'var(--color-text-light)' }}>
              Note: File processing backend is not connected yet in this initial foundation.
            </small>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Simulate Upload & Process
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
