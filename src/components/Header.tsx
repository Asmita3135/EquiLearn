import React from 'react';
import { type ProfileId, PROFILES_DATA } from '../types/profile';

interface HeaderProps {
  activeTab: 'landing' | 'select-profile' | 'workspace' | 'upload';
  onNavigate: (tab: 'landing' | 'select-profile' | 'workspace' | 'upload') => void;
  onOpenUpload: () => void;
  selectedProfile: ProfileId | null;
  isHighContrast: boolean;
  onToggleHighContrast: () => void;
  isDyslexiaFont: boolean;
  onToggleDyslexiaFont: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onNavigate,
  onOpenUpload,
  selectedProfile,
  isHighContrast,
  onToggleHighContrast,
  isDyslexiaFont,
  onToggleDyslexiaFont,
}) => {
  const currentProfileObj = PROFILES_DATA.find((p) => p.id === selectedProfile);

  return (
    <header className="site-header" role="banner">
      <div className="container">
        <div className="header-inner">
          {/* Logo & Brand */}
          <button
            type="button"
            className="brand-logo"
            onClick={() => onNavigate('landing')}
            aria-label="EquiLearn Home Page"
          >
            <span className="brand-icon" aria-hidden="true">E</span>
            <span className="brand-name">EquiLearn</span>
            <span className="brand-badge">Accessible Learning</span>
          </button>

          {/* Active Profile Badge & Change Button */}
          {currentProfileObj && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--color-primary-light)', padding: '0.35rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-primary-border)' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--color-primary)' }}>
                Active Profile: {currentProfileObj.name}
              </span>
              <button
                type="button"
                className="control-btn"
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', marginLeft: '0.25rem' }}
                onClick={() => onNavigate('select-profile')}
                aria-label={`Change current accessibility profile from ${currentProfileObj.name}`}
              >
                Change Profile
              </button>
            </div>
          )}

          {/* Navigation Menu */}
          <nav className="site-nav" role="navigation" aria-label="Main Navigation">
            <ul className="nav-list">
              <li>
                <button
                  type="button"
                  className={`nav-btn ${activeTab === 'landing' ? 'active' : ''}`}
                  onClick={() => onNavigate('landing')}
                  aria-current={activeTab === 'landing' ? 'page' : undefined}
                >
                  Home
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`nav-btn ${activeTab === 'select-profile' ? 'active' : ''}`}
                  onClick={() => onNavigate('select-profile')}
                  aria-current={activeTab === 'select-profile' ? 'page' : undefined}
                >
                  Choose Profile
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`nav-btn ${activeTab === 'workspace' ? 'active' : ''}`}
                  onClick={() => onNavigate('workspace')}
                  aria-current={activeTab === 'workspace' ? 'page' : undefined}
                >
                  Lesson Workspace
                </button>
              </li>
              <li>
                <button
                  type="button"
                  className={`nav-btn ${activeTab === 'upload' ? 'active' : ''}`}
                  onClick={onOpenUpload}
                  aria-current={activeTab === 'upload' ? 'page' : undefined}
                >
                  Upload Content
                </button>
              </li>
            </ul>
          </nav>

          {/* Accessibility Quick Toggles */}
          <div className="accessibility-controls" aria-label="Accessibility Settings">
            <button
              type="button"
              className={`control-btn ${isHighContrast ? 'active' : ''}`}
              onClick={onToggleHighContrast}
              aria-pressed={isHighContrast}
              title="Toggle High Contrast Mode"
            >
              {isHighContrast ? 'High Contrast: On' : 'High Contrast: Off'}
            </button>
            <button
              type="button"
              className={`control-btn ${isDyslexiaFont ? 'active' : ''}`}
              onClick={onToggleDyslexiaFont}
              aria-pressed={isDyslexiaFont}
              title="Toggle Dyslexia Spacing"
            >
              {isDyslexiaFont ? 'Dyslexia Spacing: On' : 'Dyslexia Spacing: Off'}
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
