"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const cleanupStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      clearTimer();
      cleanupStream();
    };
  }, [clearTimer, cleanupStream]);

  const startRecording = useCallback(async () => {
    setError(null);
    if (!navigator?.mediaDevices?.getUserMedia) {
      setError("Microphone access is not supported in this browser.");
      return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      const mimeType = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
        "audio/ogg",
      ].find((type) => MediaRecorder.isTypeSupported(type)) || "";

      const options = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start(100);
      startTimeRef.current = Date.now();
      setIsRecording(true);
      setRecordingDuration(0);

      clearTimer();
      timerRef.current = setInterval(() => {
        setRecordingDuration(Math.floor((Date.now() - startTimeRef.current) / 1000));
      }, 250);

      return true;
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Could not access microphone. Please grant permission.";
      setError(message);
      setIsRecording(false);
      clearTimer();
      cleanupStream();
      return false;
    }
  }, [clearTimer, cleanupStream]);

  const stopRecording = useCallback(async (): Promise<string | null> => {
    clearTimer();
    const mediaRecorder = mediaRecorderRef.current;
    if (!mediaRecorder || mediaRecorder.state === "inactive") {
      setIsRecording(false);
      cleanupStream();
      return null;
    }

    setIsProcessing(true);
    setIsRecording(false);

    return new Promise((resolve) => {
      mediaRecorder.onstop = () => {
        try {
          const duration = (Date.now() - startTimeRef.current) / 1000;
          if (duration < 0.4 || audioChunksRef.current.length === 0) {
            // Audio recording was a tap or too brief
            cleanupStream();
            setIsProcessing(false);
            resolve(null);
            return;
          }

          const blobType = mediaRecorder.mimeType || "audio/webm";
          const audioBlob = new Blob(audioChunksRef.current, { type: blobType });
          const reader = new FileReader();

          reader.onloadend = () => {
            const result = reader.result as string;
            // Strip out "data:audio/webm;base64," prefix to obtain raw base64 string
            const rawBase64 = result.includes(",") ? result.split(",")[1] : result;
            cleanupStream();
            setIsProcessing(false);
            resolve(rawBase64);
          };

          reader.onerror = () => {
            cleanupStream();
            setIsProcessing(false);
            resolve(null);
          };

          reader.readAsDataURL(audioBlob);
        } catch {
          cleanupStream();
          setIsProcessing(false);
          resolve(null);
        }
      };

      mediaRecorder.stop();
    });
  }, [clearTimer, cleanupStream]);

  const cancelRecording = useCallback(() => {
    clearTimer();
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    setIsProcessing(false);
    cleanupStream();
  }, [clearTimer, cleanupStream]);

  return {
    isRecording,
    recordingDuration,
    isProcessing,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
