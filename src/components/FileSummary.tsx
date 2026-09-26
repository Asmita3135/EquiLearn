import React from 'react';
import { type FileValidationResult, type UploadStatus } from '../types/upload';

interface FileSummaryProps {
  file: File;
  validation: FileValidationResult;
  status: UploadStatus;
  onClearFile: () => void;
}

export const FileSummary: React.FC<FileSummaryProps> = ({
  file,
  validation,
  status,
  onClearFile,
}) => {
  const getStatusBadge = () => {
    switch (status) {
      case 'READY':
        return (
          <span className="a11y-badge" style={{ backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary)', borderColor: 'var(--color-primary-border)' }}>
            ✓ Ready to process
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="a11y-badge" style={{ backgroundColor: '#fef3c7', color: '#92400e', borderColor: '#fcd34d' }}>
            ⏳ Simulating AI Processing...
          </span>
        );
      case 'COMPLETED_PLACEHOLDER':
        return (
          <span className="a11y-badge" style={{ backgroundColor: '#dcfce7', color: '#166534', borderColor: '#86efac' }}>
            ✓ Frontend Simulation Complete
          </span>
        );
      case 'ERROR':
        return (
          <span className="a11y-badge" style={{ backgroundColor: '#fee2e2', color: '#991b1b', borderColor: '#fca5a5' }}>
            ⚠️ Validation Error
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="file-summary-card" role="region" aria-label="Selected File Summary">
      <div className="summary-header">
        <div>
          <span className="section-tag" style={{ marginBottom: '0.4rem' }}>
            File Selected
          </span>
          <h3 className="summary-filename" style={{ fontSize: '1.25rem', margin: 0, wordBreak: 'break-all' }}>
            {file.name}
          </h3>
        </div>

        <button
          type="button"
          className="btn-secondary"
          onClick={onClearFile}
          aria-label={`Remove selected file ${file.name}`}
          style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}
        >
          Remove File
        </button>
      </div>

      <div className="summary-grid">
        <div className="summary-item">
          <span className="summary-label">Selected File:</span>
          <span className="summary-value">{file.name}</span>
        </div>

        <div className="summary-item">
          <span className="summary-label">Type:</span>
          <span className="summary-value">{validation.categoryLabel}</span>
        </div>

        <div className="summary-item">
          <span className="summary-label">Size:</span>
          <span className="summary-value">{validation.formattedSize}</span>
        </div>

        <div className="summary-item">
          <span className="summary-label">Status:</span>
          <span className="summary-value">{getStatusBadge()}</span>
        </div>
      </div>

      {/* Content Type Future Processing Explanation */}
      {validation.isValid && (
        <div className="processing-explanation-box">
          <div className="explanation-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem', fontWeight: 700 }}>
            <span aria-hidden="true">ℹ️</span>
            <span>Future AI Pipeline Behavior</span>
          </div>
          <p style={{ margin: 0, fontSize: '0.925rem', color: 'var(--color-text-main)', lineHeight: 1.5 }}>
            {validation.explanation}
          </p>
        </div>
      )}

      {/* Validation Error Announcement */}
      {!validation.isValid && validation.errorMessage && (
        <div className="validation-error-box" role="alert" aria-live="assertive">
          <span aria-hidden="true" style={{ fontSize: '1.25rem' }}>⚠️</span>
          <div>
            <strong>Error: </strong>
            {validation.errorMessage}
          </div>
        </div>
      )}
    </div>
  );
};
