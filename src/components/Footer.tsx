import React from 'react';

interface FooterProps {
  onNavigate: (tab: 'landing' | 'select-profile' | 'workspace' | 'upload') => void;
  onOpenUpload: () => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate, onOpenUpload }) => {
  return (
    <footer className="site-footer" role="contentinfo">
      <div className="container">
        <div className="footer-inner">
          <div className="footer-top">
            <div className="footer-brand">
              <div className="brand-logo" style={{ marginBottom: '0.75rem' }}>
                <span className="brand-icon" aria-hidden="true">E</span>
                <span className="brand-name">EquiLearn</span>
              </div>
              <p style={{ fontSize: '0.95rem' }}>
                Empowering every learner with accessible, multi-sensory educational experiences. Built with Universal Design for Learning (UDL) principles.
              </p>
            </div>

            <div className="footer-nav-group">
              <div>
                <h2 className="footer-heading">Navigation</h2>
                <ul className="footer-links">
                  <li>
                    <button type="button" onClick={() => onNavigate('landing')}>
                      Home Page
                    </button>
                  </li>
                  <li>
                    <button type="button" onClick={() => onNavigate('select-profile')}>
                      Choose Profile
                    </button>
                  </li>
                  <li>
                    <button type="button" onClick={() => onNavigate('workspace')}>
                      Lesson Workspace
                    </button>
                  </li>
                  <li>
                    <button type="button" onClick={onOpenUpload}>
                      Upload Content
                    </button>
                  </li>
                </ul>
              </div>

              <div>
                <h2 className="footer-heading">Supported Learning Profiles</h2>
                <ul className="footer-links">
                  <li><span>Blind (Audio-First)</span></li>
                  <li><span>Low Vision (High Contrast)</span></li>
                  <li><span>Deaf / Hard of Hearing (Captions & Visuals)</span></li>
                  <li><span>Dyslexia (Accessible Typography & Chunks)</span></li>
                </ul>
              </div>
            </div>
          </div>

          <div className="footer-bottom">
            <p>© {new Date().getFullYear()} EquiLearn Hackathon Project. Frontend Layer.</p>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <span className="a11y-badge">WCAG 2.1 Compliant Design</span>
              <span className="a11y-badge">Screen Reader Tested</span>
              <span className="a11y-badge">Keyboard Accessible</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};
