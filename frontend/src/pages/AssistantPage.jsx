import React, { useState, useEffect } from 'react';
import { useRobot } from '../context/RobotContext.jsx';
import AssistantConsole from '../components/AssistantConsole.jsx';
import AssistantReminders from '../components/AssistantReminders.jsx';

const AssistantPage = () => {
  const { windowsBaseUrl } = useRobot();
  const [messages, setMessages] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [voiceReady, setVoiceReady] = useState(false);

  // Load initial data
  useEffect(() => {
    loadReminders();
    checkVoiceStatus();
  }, []);

  const checkVoiceStatus = async () => {
    try {
      const response = await fetch(`${windowsBaseUrl}/api/status`);
      const data = await response.json();
      setVoiceReady(data.pi_connected && data.voice_ready);
    } catch (err) {
      console.error('Failed to check voice status:', err);
      setVoiceReady(false);
    }
  };

  const loadReminders = async () => {
    setLoading(true);
    console.log('Loading reminders from:', `${windowsBaseUrl}/api/assistant/reminders`);
    try {
      const response = await fetch(`${windowsBaseUrl}/api/assistant/reminders`);
      const data = await response.json();
      console.log('Reminders response:', { status: response.status, data });
      if (response.ok && data.reminders) {
        setReminders(data.reminders);
        console.log('Reminders loaded:', data.reminders.length);
      } else {
        console.error('Reminders API error:', data);
      }
    } catch (err) {
      console.error('Failed to load reminders:', err);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (text) => {
    setSending(true);
    setError(null);
    
    // Add user message immediately
    const userMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${windowsBaseUrl}/api/assistant/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, speak: true }),
      });

      const data = await response.json();
      
      if (response.ok) {
        // Add assistant response
        const assistantMessage = {
          role: 'assistant',
          content: data.response || 'Message sent to Pi speaker',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(data.message || 'Failed to send message');
      }
    } catch (err) {
      setError(err.message);
      // Remove the user message if sending failed
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  };

  const createReminder = async (reminderData) => {
    console.log('Creating reminder:', reminderData);
    try {
      const payload = {
        message: reminderData.message,
        ...(reminderData.remindAt ? 
          { remind_at: reminderData.remindAt } : 
          { delay_seconds: (reminderData.delayMinutes || 5) * 60 }
        ),
        ...(reminderData.voiceNote && { voice_note: reminderData.voiceNote }),
      };

      console.log('Reminder payload:', payload);
      console.log('Sending to:', `${windowsBaseUrl}/api/assistant/reminders`);

      const response = await fetch(`${windowsBaseUrl}/api/assistant/reminders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      console.log('Create reminder response:', { status: response.status, data });
      
      if (response.ok) {
        await loadReminders(); // Reload reminders
        return data;
      } else {
        console.error('Create reminder error:', data);
        throw new Error(data.message || 'Failed to create reminder');
      }
    } catch (err) {
      console.error('Create reminder exception:', err);
      throw new Error(err.message || 'Network error creating reminder');
    }
  };

  const deleteReminder = async (id) => {
    try {
      const response = await fetch(`${windowsBaseUrl}/api/assistant/reminders/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        await loadReminders(); // Reload reminders
      } else {
        const data = await response.json();
        throw new Error(data.message || 'Failed to delete reminder');
      }
    } catch (err) {
      console.error('Failed to delete reminder:', err);
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0a0b1f] via-[#111225] to-[#1a1b2f] px-6 py-12">
      <div className="mx-auto max-w-7xl space-y-12">
        {/* Header Section */}
        <div className="text-center">
          <h1 className="font-display text-4xl font-bold text-foreground mb-4">
            🤖 Voice Assistant & Reminder Center
          </h1>
          <p className="text-lg text-muted max-w-2xl mx-auto">
            Send Hindi voice commands and schedule smart reminders 
            that play automatically through the Pi speaker.
          </p>
        </div>

        {/* Main Features Grid */}
        <section className="grid gap-8 xl:grid-cols-[1fr,1fr]">
          {/* Left Column - Voice Assistant */}
          <div className="space-y-8">
            <AssistantConsole
              messages={messages}
              onSend={sendMessage}
              sending={sending}
              error={error}
              voiceReady={voiceReady}
            />
          </div>

          {/* Right Column - Smart Reminders */}
          <div className="space-y-8">
            <AssistantReminders
              reminders={reminders}
              onCreate={createReminder}
              onDelete={deleteReminder}
              loading={loading}
            />

            {/* Feature Overview */}
            <div className="rounded-3xl border border-white/5 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-lg">
              <h3 className="font-display text-2xl text-foreground mb-6">🎯 Assistant Features</h3>
              <div className="space-y-4 text-sm">
                <div className="rounded-2xl border border-success/20 bg-success/10 p-4">
                  <div className="font-semibold text-success mb-2">🔊 Multi-Engine Hindi TTS</div>
                  <p className="text-success/80">Enhanced text-to-speech with gTTS for quality, pyttsx3 for offline use, and espeak as fallback.</p>
                </div>
                <div className="rounded-2xl border border-warning/20 bg-warning/10 p-4">
                  <div className="font-semibold text-warning mb-2">⏰ Smart Reminder System</div>
                  <p className="text-warning/80">Schedule voice reminders with detailed logging and automatic delivery through the Pi speaker.</p>
                </div>
                <div className="rounded-2xl border border-purple-500/20 bg-purple-500/10 p-4">
                  <div className="font-semibold text-purple-400 mb-2">🌐 Cross-Platform Integration</div>
                  <p className="text-purple-300/80">Seamless communication between Windows laptop and Raspberry Pi through network API.</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AssistantPage;