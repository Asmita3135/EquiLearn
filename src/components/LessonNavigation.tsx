import React from 'react';

interface LessonNavigationProps {
  currentLessonNumber: number;
  totalLessons: number;
  onPreviousLesson: () => void;
  onNextLesson: () => void;
}

export const LessonNavigation: React.FC<LessonNavigationProps> = ({
  currentLessonNumber,
  totalLessons,
  onPreviousLesson,
  onNextLesson,
}) => {
  return (
    <nav className="lesson-nav-bar" aria-label="Lesson sequence navigation">
      <button
        type="button"
        className="btn-secondary"
        onClick={onPreviousLesson}
        disabled={currentLessonNumber <= 1}
        aria-disabled={currentLessonNumber <= 1}
      >
        ← Previous Lesson
      </button>

      <div className="lesson-progress-indicator" aria-label={`Current position: Lesson ${currentLessonNumber} of ${totalLessons}`}>
        <span className="progress-text">
          Lesson <strong>{currentLessonNumber}</strong> of <strong>{totalLessons}</strong>
        </span>
      </div>

      <button
        type="button"
        className="btn-primary"
        onClick={onNextLesson}
        disabled={currentLessonNumber >= totalLessons}
        aria-disabled={currentLessonNumber >= totalLessons}
      >
        Next Lesson →
      </button>
    </nav>
  );
};
