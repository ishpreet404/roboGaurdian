import React from 'react';
import { Link } from 'react-router-dom';
import {
  RocketLaunchIcon,
  SparklesIcon,
  ArrowRightCircleIcon
} from '@heroicons/react/24/solid';
import { ShieldCheckIcon, WifiIcon, SpeakerWaveIcon } from '@heroicons/react/24/outline';

const features = [
  {
    icon: ShieldCheckIcon,
    title: 'Safety-first autonomy',
    text: 'Monitor health metrics, alerts, and emergency stops in one glance.'
  },
  {
    icon: WifiIcon,
    title: 'Seamless connectivity',
    text: 'Synced Raspberry Pi telemetry with the Windows AI command bridge.'
  },
  {
    icon: SpeakerWaveIcon,
    title: 'Hindi voice companion',
    text: 'Greet and guide users with Chirpy—the friendly Devanagari assistant.'
  }
];

const LandingPage = () => {
  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-surface via-[#070a1d] to-[#02030c] text-foreground">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[55vh] bg-[radial-gradient(circle_at_top,_rgba(124,92,255,0.5),_transparent_70%)]" />
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-40" />

      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-20 sm:px-8 lg:px-12">
        <header className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="gradient-ring flex h-12 w-12 items-center justify-center rounded-2xl bg-[#12142c]">
              <SparklesIcon className="h-7 w-7 text-accent" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-muted">Robot Guardian</p>
              <h1 className="font-display text-2xl font-semibold">Guardian One</h1>
            </div>
          </div>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm font-medium text-muted transition hover:border-accent hover:bg-accent/20 hover:text-white"
          >
            Enter dashboard
            <ArrowRightCircleIcon className="h-4 w-4" />
          </Link>
        </header>

        <main className="mt-16 grid flex-1 gap-16 lg:grid-cols-[1.25fr_1fr]">
          <div className="space-y-10">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-4 py-1 text-xs uppercase tracking-[0.35em] text-muted">
              <RocketLaunchIcon className="h-4 w-4 text-accent" />
              Pi + Windows hybrid control
            </span>
            <h2 className="font-display text-4xl leading-tight text-foreground sm:text-5xl lg:text-[52px]">
              Orchestrate your robot guardian with cinematic clarity and live command feedback.
            </h2>
            <p className="max-w-xl text-lg text-muted">
              Launch the Command Center to supervise telemetry, stream the onboard camera, dispatch manual maneuvers, and triage alerts—all wrapped inside a responsive experience engineered for live demos.
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 rounded-full bg-accent px-6 py-3 font-display text-sm font-semibold text-white shadow-glow transition hover:bg-accentSoft"
              >
                Go to Command Center
                <ArrowRightCircleIcon className="h-5 w-5" />
              </Link>
              <a
                href="#features"
                className="inline-flex items-center gap-2 text-sm font-medium text-muted transition hover:text-foreground"
              >
                Explore features
              </a>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 rounded-[40px] bg-gradient-to-br from-accent/40 via-transparent to-sky-500/20 blur-3xl" />
            <div className="relative flex h-full flex-col justify-between rounded-[32px] border border-white/10 bg-[#0d1023]/80 p-8 shadow-card backdrop-blur-lg">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-muted">
                <p className="mb-3 text-xs uppercase tracking-[0.35em] text-muted">Demo runbook</p>
                <p className="font-display text-2xl text-foreground">Pair your Pi, power the Windows AI bridge, and press launch.</p>
              </div>
              <ul className="mt-6 space-y-4 text-sm text-muted">
                <li>• Raspberry Pi supervisor bundles the camera stream and Chirpy voice.</li>
                <li>• Windows supervisor exposes REST endpoints for the React dashboard.</li>
                <li>• One command center unifies monitoring, manual control, and alerts.</li>
              </ul>
            </div>
          </div>
        </main>

        <section id="features" className="mt-24 grid gap-7 md:grid-cols-3">
          {features.map(feature => (
            <div
              key={feature.title}
              className="rounded-3xl border border-white/5 bg-[#0d1023]/70 p-6 shadow-card backdrop-blur-lg transition hover:-translate-y-1 hover:border-accent/40 hover:bg-[#181c3b]"
            >
              <div className="gradient-ring mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5 text-accent">
                <feature.icon className="h-5 w-5" />
              </div>
              <h3 className="font-display text-lg text-foreground">{feature.title}</h3>
              <p className="mt-2 text-sm text-muted">{feature.text}</p>
            </div>
          ))}
        </section>
      </div>

      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-[35vh] bg-[radial-gradient(circle_at_bottom,_rgba(20,205,255,0.35),_transparent_70%)]" />
    </div>
  );
};

export default LandingPage;
