import React from 'react';

interface NotificationBannerProps {
  message: string | null;
  onClear: () => void;
}

export const NotificationBanner: React.FC<NotificationBannerProps> = ({ message, onClear }) => {
  if (!message) return null;

  return (
    <div
      className="notification-toast"
      role="status"
      aria-live="polite"
    >
      <span aria-hidden="true" style={{ fontSize: '1.2rem' }}>ℹ️</span>
      <div style={{ flex: 1, fontSize: '0.9rem' }}>{message}</div>
      <button
        type="button"
        className="toast-close-btn"
        onClick={onClear}
        aria-label="Dismiss notification"
      >
        Dismiss
      </button>
    </div>
  );
};
