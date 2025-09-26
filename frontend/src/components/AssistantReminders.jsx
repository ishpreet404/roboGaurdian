import React, { useMemo, useState } from "react";
import { TrashIcon, BellAlertIcon, SparklesIcon } from "@heroicons/react/24/outline";
import { motion, AnimatePresence } from "framer-motion";

const ReminderItem = ({ reminder, onDelete }) => {
  const dueLabel = useMemo(() => {
    if (!reminder.remindAt) return "—";
    try {
      const date = new Date(reminder.remindAt);
      return new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(date);
    } catch {
      return reminder.remindAt;
    }
  }, [reminder.remindAt]);

  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className="flex items-start justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm"
    >
      <div>
        <p className="font-semibold text-foreground">{reminder.message}</p>
        <p className="text-xs uppercase tracking-[0.25em] text-muted">
          {reminder.delivered ? "Delivered" : "Scheduled"} · {dueLabel}
        </p>
        {reminder.voiceNote && (
          <p className="mt-2 text-xs text-muted">🎧 Voice note: {reminder.voiceNote}</p>
        )}
      </div>
      <button
        onClick={() => onDelete(reminder.id)}
        className="rounded-full border border-danger/30 bg-danger/10 p-2 text-danger transition hover:bg-danger/20"
        title="Delete reminder"
      >
        <TrashIcon className="h-4 w-4" />
      </button>
    </motion.li>
  );
};

const AssistantReminders = ({ reminders, onCreate, onDelete, loading }) => {
  const [message, setMessage] = useState("");
  const [datetime, setDatetime] = useState("");
  const [voiceNote, setVoiceNote] = useState("");
  const [quickDelay, setQuickDelay] = useState("5");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError(null);

    if (!message.trim()) {
      setFormError("Reminder message cannot be empty.");
      return;
    }

    setSaving(true);
    try {
      await onCreate({
        message: message.trim(),
        remindAt: datetime || undefined,
        delayMinutes: !datetime ? Number(quickDelay || 5) : undefined,
        voiceNote: voiceNote.trim() || undefined,
      });
      setMessage("");
      setDatetime("");
      setVoiceNote("");
    } catch (error) {
      setFormError(error?.message || "Unable to create reminder.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-3xl border border-white/5 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-lg">
      <div className="mb-6 flex items-center gap-4">
        <div className="gradient-ring flex h-12 w-12 items-center justify-center rounded-2xl bg-success/10 text-success border border-success/20">
          <BellAlertIcon className="h-6 w-6" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-muted">Smart reminders</p>
          <h3 className="font-display text-2xl text-foreground">Voice Note Scheduler</h3>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-xs uppercase tracking-[0.25em] text-muted">Reminder message</label>
          <textarea
            className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-foreground placeholder-muted outline-none transition focus:border-accent focus:bg-white/10"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Example: 20 मिनट बाद पानी पिलाना है"
            rows={2}
          />
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs uppercase tracking-[0.25em] text-muted">Schedule (optional)</label>
            <input
              type="datetime-local"
              className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-foreground outline-none transition focus:border-accent focus:bg-white/10"
              value={datetime}
              onChange={(event) => setDatetime(event.target.value)}
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-[0.25em] text-muted">Quick delay (minutes)</label>
            <select
              disabled={Boolean(datetime)}
              className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-foreground outline-none transition focus:border-accent focus:bg-white/10 disabled:opacity-60"
              value={quickDelay}
              onChange={(event) => setQuickDelay(event.target.value)}
            >
              {[5, 10, 15, 30, 60].map((option) => (
                <option key={option} value={option}>
                  {option} minutes
                </option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="text-xs uppercase tracking-[0.25em] text-muted">Voice note (optional)</label>
          <input
            className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-foreground placeholder-muted outline-none transition focus:border-accent focus:bg-white/10"
            value={voiceNote}
            onChange={(event) => setVoiceNote(event.target.value)}
            placeholder="Text to be spoken during the reminder"
          />
        </div>

        {formError && (
          <div className="rounded-2xl border border-danger/20 bg-danger/10 px-4 py-2 text-sm text-danger">
            {formError}
          </div>
        )}

        <motion.button
          type="submit"
          whileTap={{ scale: 0.98 }}
          disabled={saving}
          className="inline-flex items-center gap-2 rounded-full bg-success px-5 py-3 text-sm font-semibold text-white shadow-glow transition hover:bg-success/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <SparklesIcon className="h-4 w-4" />
          {saving ? "Scheduling…" : "Save Reminder"}
        </motion.button>
      </form>

      <div className="mt-8">
        <p className="text-xs uppercase tracking-[0.25em] text-muted">Upcoming reminders</p>
        <div className="mt-3 rounded-2xl border border-white/5 bg-[#12142c]/60 p-4">
          {loading ? (
            <div className="py-6 text-center text-sm text-muted">Loading…</div>
          ) : reminders.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted">No reminders set.</div>
          ) : (
            <ul className="space-y-3">
              <AnimatePresence initial={false}>
                {reminders.map((reminder) => (
                  <ReminderItem
                    key={reminder.id}
                    reminder={reminder}
                    onDelete={onDelete}
                  />
                ))}
              </AnimatePresence>
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssistantReminders;
