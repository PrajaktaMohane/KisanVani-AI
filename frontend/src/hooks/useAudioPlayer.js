import { useState, useRef, useEffect, useCallback } from 'react';
import { base64ToAudioUrl } from '../utils/audioHelpers';

export function useAudioPlayer() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const audioRef = useRef(null);

  const playAudioFromBase64 = useCallback((base64Data, autoPlay = true) => {
    if (!base64Data) return;

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    const audioUrl = base64ToAudioUrl(base64Data);
    const audio = new Audio(audioUrl);
    audio.playbackRate = playbackSpeed;

    audio.onplay = () => setIsPlaying(true);
    audio.onended = () => setIsPlaying(false);
    audio.onpause = () => setIsPlaying(false);
    audio.onerror = (e) => {
      console.error('Audio playback error:', e);
      setIsPlaying(false);
    };

    audioRef.current = audio;

    if (autoPlay) {
      audio.play().catch((err) => {
        console.warn('Auto-play blocked by browser policy:', err);
        setIsPlaying(false);
      });
    }
  }, [playbackSpeed]);

  const togglePlayPause = useCallback(() => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
  }, [isPlaying]);

  const changeSpeed = useCallback((speed) => {
    setPlaybackSpeed(speed);
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  return {
    isPlaying,
    playbackSpeed,
    playAudioFromBase64,
    togglePlayPause,
    changeSpeed,
    stop,
  };
}
