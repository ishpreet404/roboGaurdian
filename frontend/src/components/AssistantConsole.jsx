import React, { useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  PaperAirplaneIcon,
  MicrophoneIcon,
  BoltIcon,
} from "@heroicons/react/24/solid";

const roleStyles = {
  user: {
    alignment: "items-end",
    bubble: "bg-accent/20 border border-accent/40 text-accent",
  },
  assistant: {
    alignment: "items-start",
    bubble: "bg-white/10 border border-white/10 text-foreground",
  },
};

const MessageBubble = ({ role, content, timestamp }) => {
  const { alignment, bubble } = roleStyles[role] || roleStyles.assistant;
  const timeLabel = useMemo(() => {
    if (!timestamp) return null;
    try {
      const date = new Date(timestamp);
      return new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
      }).format(date);
    } catch {
      return null;
    }
  }, [timestamp]);

  return (
    <motion.div
      className={`flex ${alignment}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      layout
    >
      <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm ${bubble}`}>
        <p className="whitespace-pre-line leading-relaxed">{content}</p>
        {timeLabel && (
          <span className="mt-2 block text-[11px] uppercase tracking-[0.25em] text-white/60">
            {timeLabel}
          </span>
        )}
      </div>
    </motion.div>
  );
};

const FALLBACK_MODES = [
  {
    id: "care_companion",
    label: "Care Companion",
    description:
      "रिमाइंडर, हल्की बातचीत और नरम सूचनाएँ सक्रिय रहती हैं।",
  },
  {
    id: "watchdog",
    label: "Watchdog",
    description:
      "सुरक्षा चौकसी: कोई हरकत मिलते ही तेज़ अलार्म बजता है।",
  },
  {
    id: "edumate",
    label: "Edumate",
    description:
      "माता-पिता के चुने हुए हिंदी पाठ और गतिविधियाँ सुनाई जाती हैं।",
  },
];

const MODE_TIPS = {
  care_companion:
    "Care Companion मोड में मित्रवत बातचीत और दैनिक याद दिलाने वाली सूचनाएँ चालू रहती हैं।",
  watchdog:
    "Watchdog मोड में रोबोट स्थिर रहता है और लगातार निगरानी कर अलार्म बजाता है।",
  edumate:
    "Edumate मोड में आप पाठ भेजते ही Chirpy उसे ज़ोर से पढ़कर सुनाता है।",
};

const AssistantConsole = ({
  messages,
  onSend,
  sending,
  error,
  voiceReady,
  mode,
  modeMetadata = {},
  availableModes,
  onModeSelect,
  updatingMode = false,
  modeError,
  onSilenceAlarm = () => {},
  watchdogAlarmActive = false,
}) => {
  const [draft, setDraft] = useState("");
  const listRef = useRef(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!draft.trim()) return;
    const current = draft;
    setDraft("");
    try {
      await onSend(current);
      if (listRef.current) {
        requestAnimationFrame(() => {
          listRef.current.scrollTop = listRef.current.scrollHeight;
        });
      }
    } catch (sendError) {
      console.error(sendError);
      setDraft(current);
    }
  };

  const modeOptions = useMemo(() => {
    if (Array.isArray(availableModes) && availableModes.length > 0) {
      return availableModes.map((item) => ({
        id: item.id,
        label: item.label || item.id,
        description: item.description,
      }));
    }
    return FALLBACK_MODES;
  }, [availableModes]);

  const normalizedMode = (mode || "care_companion").toLowerCase();
  const activeMode = modeOptions.find((option) => option.id === normalizedMode) || modeOptions[0];
  const modeTip = MODE_TIPS[normalizedMode] || activeMode?.description;
  const latestLesson = modeMetadata?.last_prompt;
  const lessonTime = modeMetadata?.last_prompt_at;
  const lessonTimeLabel = useMemo(() => {
    if (!lessonTime) return null;
    const parsed = new Date(lessonTime);
    if (Number.isNaN(parsed.getTime())) {
      return null;
    }
    return parsed.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  }, [lessonTime]);

  return (
    <div className="rounded-3xl border border-white/5 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-lg">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-muted">Voice companion</p>
          <h3 className="font-display text-2xl text-foreground">Chirpy Assistant</h3>
        </div>
        <span
          className={`flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${
            voiceReady
              ? "bg-success/15 text-success"
              : "bg-warning/15 text-warning"
          }`}
        >
          <MicrophoneIcon className="h-4 w-4" />
          {voiceReady ? "Speaker Ready" : "Speaker Offline"}
        </span>
      </div>

      <div className="mb-6 rounded-2xl border border-white/10 bg-white/5 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-muted">Operating mode</p>
            <div className="mt-1 flex items-center gap-2 text-sm font-semibold text-foreground">
              <BoltIcon className="h-4 w-4 text-accent" />
              <span>{activeMode?.label || "Care Companion"}</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {modeOptions.map((option) => {
              const isActive = option.id === normalizedMode;
              return (
                <button
                  key={option.id}
                  type="button"
                  onClick={() =>
                    !isActive && !updatingMode && onModeSelect?.(option.id)
                  }
                  disabled={isActive || updatingMode}
                  className={`rounded-full px-4 py-2 text-xs font-semibold transition focus:outline-none focus:ring-2 focus:ring-accent/60 ${
                    isActive
                      ? "bg-accent text-white shadow-glow"
                      : "bg-white/10 text-muted hover:bg-white/20"
                  } ${updatingMode && !isActive ? "opacity-60" : ""}`}
                >
                  {isActive ? "Active" : option.label}
                </button>
              );
            })}
          </div>
        </div>

        {modeTip && (
          <p className="mt-3 text-xs text-muted">{modeTip}</p>
        )}

        {normalizedMode === "edumate" && latestLesson && (
          <div className="mt-3 rounded-xl border border-accent/30 bg-accent/10 px-3 py-2 text-xs text-accent">
            <p className="font-semibold">नवीनतम पाठ</p>
            <p className="mt-1 text-foreground/90">{latestLesson}</p>
            {lessonTimeLabel && (
              <p className="mt-1 text-[11px] uppercase tracking-[0.2em] text-muted">
                {lessonTimeLabel}
              </p>
            )}
          </div>
        )}

        {watchdogAlarmActive && (
          <div className="mt-3 flex flex-col gap-2 rounded-xl border border-danger/40 bg-danger/10 px-3 py-3 text-danger sm:flex-row sm:items-center sm:justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.2em]">
              अलार्म बज रहा है!
            </span>
            <button
              type="button"
              onClick={onSilenceAlarm}
              disabled={updatingMode}
              className="rounded-full bg-danger px-4 py-2 text-xs font-semibold text-white shadow transition hover:bg-danger/90 disabled:opacity-60"
            >
              अलार्म बंद करें
            </button>
          </div>
        )}

        {modeError && (
          <div className="mt-3 rounded-xl border border-danger/40 bg-danger/10 px-3 py-2 text-xs text-danger">
            {modeError}
          </div>
        )}
      </div>

      <div
        ref={listRef}
        className="mb-6 max-h-96 space-y-4 overflow-y-auto rounded-2xl border border-white/5 bg-[#12142c]/70 p-5"
      >
        <AnimatePresence initial={false}>
          {messages.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.7 }}
              className="rounded-xl border border-dashed border-white/10 bg-white/5 p-6 text-center text-sm text-muted"
            >
              Assistant idle. Say "नमस्ते" to begin in Hindi.
            </motion.div>
          ) : (
            messages.map((message, index) => (
              <MessageBubble
                key={`${message.role}-${index}-${message.timestamp || index}`}
                role={message.role}
                content={message.content}
                timestamp={message.timestamp}
              />
            ))
          )}
        </AnimatePresence>
      </div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 rounded-2xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
        >
          {error}
        </motion.div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <textarea
          className="min-h-[96px] w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-foreground placeholder-muted outline-none transition focus:border-accent focus:bg-white/10"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="हिंदी में अपना संदेश लिखें..."
        />
        <motion.button
          type="submit"
          whileTap={{ scale: 0.98 }}
          disabled={sending}
          className="inline-flex items-center justify-center gap-2 rounded-full bg-accent px-5 py-3 text-sm font-semibold text-white shadow-glow transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <PaperAirplaneIcon className="h-4 w-4" />
          {sending ? "Sending…" : "Send to Chirpy"}
        </motion.button>
      </form>
    </div>
  );
};

export default AssistantConsole;
