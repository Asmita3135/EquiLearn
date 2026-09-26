import React, { useRef, useState } from 'react';
import { SUPPORTED_EXTENSIONS } from '../types/upload';

interface FileDropZoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export const FileDropZone: React.FC<FileDropZoneProps> = ({ onFileSelected, disabled = false }) => {
  const [isDragActive, setIsDragActive] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragActive(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      onFileSelected(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = e.target.files[0];
      onFileSelected(selected);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div
      className={`file-drop-zone ${isDragActive ? 'drag-active' : ''} ${disabled ? 'drop-zone-disabled' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      role="region"
      aria-label="File drag and drop upload region"
    >
      {/* Hidden Native Input */}
      <input
        ref={fileInputRef}
        type="file"
        id="equilearn-file-input"
        accept={SUPPORTED_EXTENSIONS.join(',')}
        onChange={handleFileChange}
        className="sr-only"
        disabled={disabled}
      />

      <div className="drop-zone-content">
        <div className="drop-icon-wrapper" aria-hidden="true">
          📁
        </div>

        <h3 style={{ fontSize: '1.2rem', marginBottom: '0.4rem' }}>
          Drag and drop your learning content here
        </h3>

        <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.25rem', fontSize: '0.95rem' }}>
          or choose a file from your device
        </p>

        <button
          type="button"
          className="btn-primary"
          onClick={handleButtonClick}
          disabled={disabled}
          aria-label="Choose a file from your device file picker"
        >
          Choose a File
        </button>

        <div className="supported-formats-list" style={{ marginTop: '1.5rem', fontSize: '0.85rem', color: 'var(--color-text-light)' }}>
          <strong>Accepted Formats:</strong> PDF (.pdf), Video (.mp4, .mov, .avi), Audio (.mp3, .wav, .m4a), Text (.txt)
        </div>
      </div>
    </div>
  );
};
