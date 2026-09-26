import React, { useState, useEffect, useRef } from 'react';
import { type LessonData } from '../types/lesson';

interface AudioPlayerProps {
  lessonData: LessonData;
  currentTime: number;
  onSeek: (time: number) => void;
  onShowNotification: (message: string) => void;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  lessonData,
  currentTime,
  onSeek,
  onShowNotification,
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [volume, setVolume] = useState<number>(80);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<string>('1.0');
  const [audioError, setAudioError] = useState<boolean>(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioSrc = lessonData.audio.src;
  const duration = lessonData.audio.duration || 60;

  // Sync seek position when parent calls onSeek / currentTime changes externally
  useEffect(() => {
    if (audioRef.current && Math.abs(audioRef.current.currentTime - currentTime) > 1.5) {
      audioRef.current.currentTime = currentTime;
    }
  }, [currentTime]);

  // Sync playback speed
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = parseFloat(playbackSpeed);
    }
  }, [playbackSpeed]);

  // Sync volume & mute state
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume / 100;
    }
  }, [volume, isMuted]);

  // Format seconds into MM:SS format
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTogglePlay = () => {
    if (!audioSrc || audioError) {
      const newIsPlaying = !isPlaying;
      setIsPlaying(newIsPlaying);
      onShowNotification(newIsPlaying ? 'Simulated audio playback started.' : 'Audio playback paused.');
      return;
    }

    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
        onShowNotification('Audio playback paused.');
      } else {
        audioRef.current
          .play()
          .then(() => {
            setIsPlaying(true);
            onShowNotification('Playing Member 2 synthesized TTS audio.');
          })
          .catch((err) => {
            loggerError(err);
            setAudioError(true);
            setIsPlaying(false);
            onShowNotification('Audio stream play error. Showing fallback controls.');
          });
      }
    }
  };

  const loggerError = (err: unknown) => {
    console.warn('Audio element error:', err);
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      onSeek(audioRef.current.currentTime);
    }
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
    onSeek(0);
    onShowNotification('Audio playback completed.');
  };

  const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value);
    onSeek(newTime);
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
    }
  };

  const handleSpeedChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const speed = e.target.value;
    setPlaybackSpeed(speed);
    onShowNotification(`Playback speed set to ${speed}x.`);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    setVolume(val);
    if (val === 0) {
      setIsMuted(true);
    } else if (isMuted) {
      setIsMuted(false);
    }
  };

  const handleToggleMute = () => {
    setIsMuted(!isMuted);
  };

  const handlePrevious = () => {
    onSeek(0);
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
    }
    onShowNotification('Reset audio position to beginning.');
  };

  const handleNext = () => {
    const nextTime = Math.min(duration, currentTime + 15);
    onSeek(nextTime);
    if (audioRef.current) {
      audioRef.current.currentTime = nextTime;
    }
    onShowNotification('Skipped forward 15 seconds.');
  };

  return (
    <section className="audio-player-card" aria-labelledby="audio-player-heading">
      {/* Hidden Real HTML5 Audio Element */}
      {audioSrc && !audioError && (
        <audio
          ref={audioRef}
          src={audioSrc}
          onTimeUpdate={handleTimeUpdate}
          onEnded={handleAudioEnded}
          onError={() => setAudioError(true)}
          preload="metadata"
        />
      )}

      <div className="audio-player-header">
        <div>
          <span className="a11y-badge" style={{ marginBottom: '0.4rem' }}>
            {audioSrc && !audioError ? 'Member 2 Audio Stream' : 'Audio Player'}
          </span>
          <h2 id="audio-player-heading" style={{ fontSize: '1.25rem', margin: 0 }}>
            {lessonData.audio.title}
          </h2>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--color-text-light)', fontWeight: 600 }}>
          {isPlaying ? '▶ Playing' : '⏸ Paused'}
        </div>
      </div>

      {/* Graceful Audio Unavailable State Notice if no audio or load error */}
      {(!audioSrc || audioError) && (
        <div
          style={{
            padding: '0.75rem 1rem',
            backgroundColor: 'var(--color-bg)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '1rem',
            fontSize: '0.875rem',
            color: 'var(--color-text-muted)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <span aria-hidden="true">ℹ️</span>
          <span>Audio stream notice: Simulated frontend playback active.</span>
        </div>
      )}

      {/* Progress & Time Controls */}
      <div className="seek-container">
        <div className="time-display" aria-label="Current time and duration">
          <span className="time-current">{formatTime(currentTime)}</span>
          <span className="time-total">/ {formatTime(duration)}</span>
        </div>

        <div className="seek-slider-wrapper">
          <label htmlFor="audio-seek-slider" className="sr-only">
            Seek audio progress position
          </label>
          <input
            id="audio-seek-slider"
            type="range"
            min={0}
            max={duration > 0 ? duration : 100}
            step={1}
            value={currentTime}
            onChange={handleSeekChange}
            aria-valuemin={0}
            aria-valuemax={duration > 0 ? duration : 100}
            aria-valuenow={currentTime}
            aria-valuetext={`${formatTime(currentTime)} of ${formatTime(duration)}`}
            className="audio-range-slider"
          />
        </div>
      </div>

      {/* Media Control Buttons */}
      <div className="controls-toolbar">
        <div className="playback-buttons">
          <button
            type="button"
            className="player-btn"
            onClick={handlePrevious}
            aria-label="Restart audio or skip to start"
            title="Restart audio"
          >
            <span aria-hidden="true">⏮</span>
            <span className="btn-label">Restart</span>
          </button>

          <button
            type="button"
            className="player-btn play-pause-btn btn-primary"
            onClick={handleTogglePlay}
            aria-label={isPlaying ? 'Pause audio narration' : 'Play audio narration'}
            aria-pressed={isPlaying}
          >
            <span aria-hidden="true">{isPlaying ? '⏸' : '▶'}</span>
            <span>{isPlaying ? 'Pause' : 'Play'}</span>
          </button>

          <button
            type="button"
            className="player-btn"
            onClick={handleNext}
            aria-label="Skip forward 15 seconds"
            title="Skip forward 15s"
          >
            <span className="btn-label">Forward +15s</span>
            <span aria-hidden="true">⏭</span>
          </button>
        </div>

        {/* Speed & Volume Controls */}
        <div className="secondary-controls">
          <div className="speed-control-group">
            <label htmlFor="playback-speed-select" style={{ fontSize: '0.85rem', fontWeight: 600 }}>
              Speed:
            </label>
            <select
              id="playback-speed-select"
              value={playbackSpeed}
              onChange={handleSpeedChange}
              aria-label="Select audio playback speed"
              className="player-select"
            >
              <option value="0.75">0.75x (Slower)</option>
              <option value="1.0">1.0x (Normal)</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
              <option value="2.0">2.0x (Faster)</option>
            </select>
          </div>

          <div className="volume-control-group">
            <button
              type="button"
              className="player-btn-icon"
              onClick={handleToggleMute}
              aria-label={isMuted ? 'Unmute volume' : 'Mute volume'}
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              <span aria-hidden="true">{isMuted || volume === 0 ? '🔇' : '🔊'}</span>
            </button>
            <label htmlFor="audio-volume-slider" className="sr-only">
              Adjust audio volume level
            </label>
            <input
              id="audio-volume-slider"
              type="range"
              min={0}
              max={100}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              aria-label="Audio volume level"
              aria-valuenow={isMuted ? 0 : volume}
              aria-valuetext={`${isMuted ? 0 : volume} percent`}
              className="audio-volume-slider"
            />
          </div>
        </div>
      </div>
    </section>
  );
};
