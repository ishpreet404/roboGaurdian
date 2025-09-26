import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MicrophoneIcon,
  PlayIcon,
  StopIcon,
  PaperAirplaneIcon,
  SpeakerWaveIcon,
} from '@heroicons/react/24/solid';
import { useRobot } from '../context/RobotContext.jsx';

const AudioChat = () => {
  const { windowsBaseUrl } = useRobot();
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [status, setStatus] = useState({ message: '', type: '' });
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const recordedChunksRef = useRef([]);

  const showStatus = useCallback((message, type) => {
    setStatus({ message, type });
    setTimeout(() => setStatus({ message: '', type: '' }), 5000);
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 22050,  // Lower sample rate for better Pi compatibility
          channelCount: 1,    // Mono audio for smaller files
        },
      });

      recordedChunksRef.current = [];
      
      // Choose the best format for Pi compatibility
      let options = {};
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        options = {
          mimeType: 'audio/webm;codecs=opus',
          audioBitsPerSecond: 48000  // Good quality for speech
        };
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        options = {
          mimeType: 'audio/mp4',
          audioBitsPerSecond: 64000
        };
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        options = {
          mimeType: 'audio/webm',
          audioBitsPerSecond: 48000
        };
      }
      
      const recorder = new MediaRecorder(stream, options);
      console.log('🎤 Recording with format:', recorder.mimeType);

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) recordedChunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(recordedChunksRef.current, { 
          type: recorder.mimeType || 'audio/wav' 
        });
        setRecordedBlob(blob);
        showStatus('✅ Recording complete! You can now play or send to Pi.', 'success');
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordedBlob(null);
      showStatus('🔴 Recording... Click stop when done.', 'recording');
    } catch (err) {
      showStatus(`❌ Error accessing microphone: ${err.message}`, 'error');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      setMediaRecorder(null);
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const playRecording = () => {
    if (recordedBlob) {
      const audio = new Audio(URL.createObjectURL(recordedBlob));
      audio.play().catch(err => {
        showStatus(`❌ Error playing audio: ${err.message}`, 'error');
      });
      showStatus('▶️ Playing recorded audio locally...', 'info');
    }
  };

  const sendAudioToPi = async () => {
    if (!recordedBlob) {
      showStatus('❌ No recording to send', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('file', recordedBlob, 'mic_audio.wav');

    try {
      showStatus('📡 Sending audio to Pi speaker...', 'info');

      const response = await fetch(`${windowsBaseUrl}/api/assistant/audio-chat`, {
        method: 'POST',
        body: formData,
      });

      let result;
      const responseText = await response.text();

      try {
        result = JSON.parse(responseText);
      } catch (parseErr) {
        showStatus(
          `❌ Server returned non-JSON response (${response.status}): ${responseText.substring(0, 100)}...`,
          'error'
        );
        return;
      }

      if (response.ok) {
        showStatus(
          `✅ Audio sent successfully! Playing through Pi speaker. (${result.file_size || 'unknown size'})`,
          'success'
        );
        // Clear the recording after successful send
        setRecordedBlob(null);
      } else {
        showStatus(`❌ Failed to send audio: ${result.message}`, 'error');
      }
    } catch (err) {
      showStatus(`❌ Network error: ${err.message}`, 'error');
    }
  };

  const getStatusStyle = () => {
    switch (status.type) {
      case 'success': return 'bg-success/15 text-success border-success/30';
      case 'error': return 'bg-danger/15 text-danger border-danger/30';
      case 'recording': return 'bg-warning/15 text-warning border-warning/30';
      default: return 'bg-accent/15 text-accent border-accent/30';
    }
  };

  return (
    <div className="rounded-3xl border border-white/5 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-lg">
      <div className="mb-6">
        <p className="text-xs uppercase tracking-[0.35em] text-muted">Voice communication</p>
        <h3 className="font-display text-2xl text-foreground">Audio Chat</h3>
        <p className="mt-2 text-sm text-muted">
          Record your voice and send it directly to the Pi speaker for real-time communication.
        </p>
      </div>

      <div className="space-y-6">
        {/* Recording Controls */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <motion.button
                type="button"
                onClick={toggleRecording}
                whileTap={{ scale: 0.95 }}
                className={`flex h-16 w-16 items-center justify-center rounded-full font-semibold text-white shadow-lg transition ${
                  isRecording
                    ? 'bg-danger animate-pulse'
                    : 'bg-accent hover:bg-accent/90'
                }`}
              >
                {isRecording ? (
                  <StopIcon className="h-6 w-6" />
                ) : (
                  <MicrophoneIcon className="h-6 w-6" />
                )}
              </motion.button>
              
              <div>
                <p className="text-sm font-semibold text-foreground">
                  {isRecording ? 'Recording...' : 'Ready to Record'}
                </p>
                <p className="text-xs text-muted">
                  {isRecording ? 'Click stop when finished' : 'Click microphone to start'}
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <motion.button
                type="button"
                onClick={playRecording}
                disabled={!recordedBlob || isRecording}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm font-semibold text-foreground transition hover:bg-white/20 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <PlayIcon className="h-4 w-4" />
                Play
              </motion.button>
              
              <motion.button
                type="button"
                onClick={sendAudioToPi}
                disabled={!recordedBlob || isRecording}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 rounded-full bg-success px-4 py-2 text-sm font-semibold text-white shadow-glow transition hover:bg-success/90 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <SpeakerWaveIcon className="h-4 w-4" />
                Send to Pi
              </motion.button>
            </div>
          </div>
        </div>

        {/* Status Display */}
        <AnimatePresence>
          {status.message && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`rounded-2xl border px-4 py-3 text-sm font-medium ${getStatusStyle()}`}
            >
              {status.message}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Feature Info */}
        <div className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <h4 className="text-sm font-semibold text-foreground mb-2">How it works:</h4>
          <ul className="text-xs text-muted space-y-1">
            <li>• Record your voice using the microphone button</li>
            <li>• Preview your recording by clicking "Play"</li>
            <li>• Send the audio directly to the Pi speaker with "Send to Pi"</li>
            <li>• Perfect for real-time communication with people near the robot</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AudioChat;