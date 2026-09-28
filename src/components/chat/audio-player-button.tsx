"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Square, Volume2 } from "lucide-react";
import { requestTts } from "@/lib/sse";

type AudioPlayerButtonProps = {
  text: string;
  targetLang: string;
  cachedAudio?: string;
  onAudioFetched?: (audioBase64: string) => void;
};

export function AudioPlayerButton({
  text,
  targetLang,
  cachedAudio,
  onAudioFetched,
}: AudioPlayerButtonProps) {
  const [loading, setLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioData, setAudioData] = useState<string | undefined>(cachedAudio);
  const [error, setError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  async function handleTogglePlay() {
    setError(null);

    // If currently playing, clicking stops playback
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      return;
    }

    // If audio is already fetched and cached
    if (audioData) {
      playAudio(audioData);
      return;
    }

    // Fetch audio from TTS endpoint
    setLoading(true);
    try {
      const base64 = await requestTts(text, targetLang);
      setAudioData(base64);
      onAudioFetched?.(base64);
      playAudio(base64);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load speech.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  function playAudio(base64: string) {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    const audioSrc = "data:audio/mpeg;base64," + base64;
    const audio = new Audio(audioSrc);
    audioRef.current = audio;

    audio.onended = () => {
      setIsPlaying(false);
    };

    audio.onerror = () => {
      setIsPlaying(false);
      setError("Playback error");
    };

    audio
      .play()
      .then(() => {
        setIsPlaying(true);
      })
      .catch((err) => {
        setIsPlaying(false);
        setError("Audio playback prevented or unsupported.");
      });
  }

  return (
    <div className="inline-flex items-center gap-2">
      <button
        type="button"
        onClick={handleTogglePlay}
        disabled={loading}
        title={
          isPlaying
            ? "Stop audio playback"
            : loading
              ? "Generating speech audio..."
              : `Listen to audio in ${targetLang.toUpperCase()}`
        }
        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition-all ${
          isPlaying
            ? "border border-primary/30 bg-primary/10 text-primary animate-pulse"
            : "border border-border bg-background/80 text-muted-foreground hover:bg-accent hover:text-foreground"
        }`}
      >
        {loading ? (
          <>
            <Loader2 className="size-3.5 animate-spin text-primary" />
            <span className="text-[11px]">Generating audio…</span>
          </>
        ) : isPlaying ? (
          <>
            <span className="flex items-center gap-0.5">
              <span className="inline-block size-1 animate-bounce rounded-full bg-primary" />
              <span className="inline-block size-1 animate-bounce rounded-full bg-primary [animation-delay:150ms]" />
              <span className="inline-block size-1 animate-bounce rounded-full bg-primary [animation-delay:300ms]" />
            </span>
            <span className="text-[11px] font-semibold text-primary">Playing Audio…</span>
            <Square className="size-2.5 fill-current text-primary" />
          </>
        ) : (
          <>
            <Volume2 className="size-3.5" />
            <span className="text-[11px]">Listen</span>
          </>
        )}
      </button>

      {error ? (
        <span className="text-[11px] text-destructive" title={error}>
          TTS Unavailable
        </span>
      ) : null}
    </div>
  );
}
