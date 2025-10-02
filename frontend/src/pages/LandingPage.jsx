import React from 'react';
import { Link } from 'react-router-dom';
import {
  RocketLaunchIcon,
  SparklesIcon,
  ArrowRightCircleIcon,
  PlayIcon,
  ChevronRightIcon
} from '@heroicons/react/24/solid';
import { 
  ShieldCheckIcon, 
  WifiIcon, 
  SpeakerWaveIcon, 
  CpuChipIcon,
  VideoCameraIcon,
  CommandLineIcon,
  SignalIcon,
  BoltIcon 
} from '@heroicons/react/24/outline';

const features = [
  {
    icon: ShieldCheckIcon,
    title: 'Safety-first autonomy',
    description: 'Advanced obstacle detection with emergency stop protocols',
    details: 'Real-time hazard assessment and collision avoidance systems'
  },
  {
    icon: WifiIcon,
    title: 'Seamless connectivity',
    description: 'Hybrid Pi-Windows architecture for maximum reliability',
    details: 'Distributed processing with failover mechanisms'
  },
  {
    icon: SpeakerWaveIcon,
    title: 'Hindi voice companion',
    description: 'Chirpy assistant with natural language processing',
    details: 'Voice commands and feedback in Devanagari script'
  },
  {
    icon: CpuChipIcon,
    title: 'AI-powered vision',
    description: 'YOLOv8 object detection with real-time inference',
    details: 'Person tracking and environmental awareness'
  }
];

const specs = [
  { label: 'Processing Power', value: 'Raspberry Pi 4 + Windows AI' },
  { label: 'Vision System', value: 'YOLOv8 Neural Network' },
  { label: 'Communication', value: 'UART + REST APIs' },
  { label: 'Voice AI', value: 'Hindi Language Support' },
  { label: 'Control Range', value: 'Real-time Telemetry' },
  { label: 'Safety Features', value: 'Emergency Stop Protocol' }
];

const LandingPage = () => {
  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-surface via-surfaceAlt to-card">
      {/* Background Effects */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_50%,_rgba(124,92,255,0.15),_transparent_60%)]" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,_rgba(124,92,255,0.08),_transparent_70%)]" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_40%_90%,_rgba(124,92,255,0.06),_transparent_75%)]" />

      {/* Hero Section */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-6 py-24">
          {/* Navigation */}
          <header className="flex items-center justify-between mb-20">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-accent/60 shadow-glow">
                <SparklesIcon className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="font-display text-2xl font-bold text-foreground">Chirpy</h1>
                <p className="text-sm text-muted">Autonomous Robot System</p>
              </div>
            </div>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-accent/20 border border-accent/30 px-6 py-3 font-medium text-accent transition hover:bg-accent hover:text-white shadow-glow"
            >
              Launch Dashboard
              <ArrowRightCircleIcon className="h-5 w-5" />
            </Link>
          </header>

          {/* Hero Content */}
          <div className="grid gap-16 lg:grid-cols-2 lg:gap-24 items-center">
            <div className="space-y-8">
              <div className="inline-flex items-center gap-3 rounded-full border border-accent/30 bg-accent/10 px-4 py-2 text-sm font-medium text-accent">
                <RocketLaunchIcon className="h-4 w-4" />
                Next-Gen Robot Control Platform
              </div>
              
              <h2 className="font-display text-5xl font-bold leading-tight text-foreground lg:text-6xl">
                Meet Chirpy Your
                <span className="bg-gradient-to-r from-accent via-info to-success bg-clip-text text-transparent"> AI-Powered </span>
                Guardian
              </h2>
              
              <p className="text-xl text-muted leading-relaxed">
                Experience the future of robotics with Chirpy - an intelligent autonomous system featuring 
                real-time vision processing, voice interaction, and seamless remote control capabilities.
              </p>
              
              <div className="flex flex-wrap gap-4">
                <Link
                  to="/dashboard"
                  className="inline-flex items-center gap-3 rounded-full bg-accent px-8 py-4 font-display font-semibold text-white shadow-glow transition hover:bg-accent/90 hover:shadow-accent/50"
                >
                  <PlayIcon className="h-5 w-5" />
                  Start Command Center
                </Link>
                <a
                  href="#showcase"
                  className="inline-flex items-center gap-2 rounded-full border border-white/20 px-6 py-4 font-medium text-foreground transition hover:border-accent hover:text-accent"
                >
                  Explore Features
                  <ChevronRightIcon className="h-4 w-4" />
                </a>
              </div>
            </div>

            {/* Robot Showcase */}
            <div className="relative">
              <div className="absolute -inset-4 rounded-3xl bg-gradient-to-r from-accent/20 via-accent/15 to-accent/10 blur-2xl" />
              <div className="relative rounded-3xl border border-white/10 bg-card/80 p-8 shadow-2xl backdrop-blur-lg">
                <div className="aspect-video rounded-2xl bg-gradient-to-br from-surfaceAlt to-surface border border-white/5 overflow-hidden">
                  <img
                    src="https://media.licdn.com/dms/image/v2/D5622AQE3LOhvVTnehQ/feedshare-shrink_1280/B56ZmbbXqjHQAw-/0/1759249267915?e=1762387200&v=beta&t=r27XvGaoEX9QbMp2bfMxfmJR1mzlc6_zOYkrVim2QuM"
                    alt="Chirpy"
                    className="w-full h-full object-cover opacity-90"
                    onError={(e) => {
                      e.target.src = "https://dummyimage.com/800x600/1a1d3a/7c5cff&text=Guardian+One+Robot";
                    }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                  <div className="absolute bottom-4 left-4 right-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-display font-semibold text-white">Chirpy</p>
                        <p className="text-sm text-white/80">Status: Operational</p>
                      </div>
                      <div className="flex items-center gap-2 rounded-full bg-success/20 border border-success/40 px-3 py-1">
                        <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
                        <span className="text-xs font-medium text-success">LIVE</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Live Stats */}
                <div className="mt-6 grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-success">98%</div>
                    <div className="text-xs text-muted">System Health</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-info">24/7</div>
                    <div className="text-xs text-muted">Uptime</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-accent">AI</div>
                    <div className="text-xs text-muted">Powered</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="showcase" className="relative py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-20">
            <h3 className="font-display text-4xl font-bold text-foreground mb-6">
              Advanced Capabilities
            </h3>
            <p className="text-xl text-muted max-w-3xl mx-auto">
              Guardian One combines cutting-edge AI, robust hardware, and intuitive software 
              to deliver unmatched autonomous functionality.
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <div
                key={feature.title}
                className="group relative rounded-3xl border border-white/5 bg-card/60 p-8 shadow-card backdrop-blur-lg transition-all duration-300 hover:-translate-y-2 hover:border-accent/40 hover:shadow-accent/20"
              >
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-accent/20 to-info/20 border border-accent/30 group-hover:from-accent/40 group-hover:to-info/40 transition-all duration-300">
                  <feature.icon className="h-8 w-8 text-accent" />
                </div>
                <h4 className="font-display text-xl font-semibold text-foreground mb-3">
                  {feature.title}
                </h4>
                <p className="text-muted mb-4">{feature.description}</p>
                <p className="text-sm text-muted/80">{feature.details}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technical Specifications */}
      <section className="relative py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid gap-16 lg:grid-cols-2 items-center">
            <div>
              <h3 className="font-display text-4xl font-bold text-foreground mb-8">
                Technical Excellence
              </h3>
              <div className="space-y-6">
                {specs.map((spec, index) => (
                  <div key={spec.label} className="flex items-center justify-between py-4 border-b border-white/5">
                    <span className="font-medium text-foreground">{spec.label}</span>
                    <span className="text-accent font-mono text-sm">{spec.value}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute -inset-4 rounded-3xl bg-gradient-to-r from-accent/15 via-accent/10 to-accent/8 blur-2xl" />
              <div className="relative rounded-3xl border border-white/10 bg-card/80 p-8 shadow-2xl backdrop-blur-lg">
                <h4 className="font-display text-2xl font-semibold text-foreground mb-6">System Architecture</h4>
                <div className="space-y-4">
                  <div className="flex items-center gap-4 p-4 rounded-2xl bg-success/10 border border-success/20">
                    <VideoCameraIcon className="h-8 w-8 text-success" />
                    <div>
                      <div className="font-semibold text-success">Vision Processing</div>
                      <div className="text-sm text-muted">Real-time object detection & tracking</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 p-4 rounded-2xl bg-accent/10 border border-accent/20">
                    <CommandLineIcon className="h-8 w-8 text-accent" />
                    <div>
                      <div className="font-semibold text-accent">Command Interface</div>
                      <div className="text-sm text-muted">Intuitive dashboard & voice control</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 p-4 rounded-2xl bg-info/10 border border-info/20">
                    <SignalIcon className="h-8 w-8 text-info" />
                    <div>
                      <div className="font-semibold text-info">Communication Hub</div>
                      <div className="text-sm text-muted">Multi-protocol connectivity</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="relative py-24">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <div className="rounded-3xl border border-white/10 bg-card/80 p-12 shadow-2xl backdrop-blur-lg">
            <h3 className="font-display text-4xl font-bold text-foreground mb-6">
              Ready to Command Your Guardian?
            </h3>
            <p className="text-xl text-muted mb-8 max-w-2xl mx-auto">
              Experience the next generation of autonomous robotics. Launch the command center 
              and take control of your AI-powered guardian today.
            </p>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-accent to-info px-10 py-4 font-display text-lg font-semibold text-white shadow-glow transition hover:shadow-accent/50"
            >
              <RocketLaunchIcon className="h-6 w-6" />
              Launch Command Center
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative py-12 border-t border-white/5">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/20">
                <SparklesIcon className="h-6 w-6 text-accent" />
              </div>
              <div>
                <div className="font-display font-semibold text-foreground">Guardian One</div>
                <div className="text-sm text-muted">Autonomous Robot System</div>
              </div>
            </div>
            <div className="text-sm text-muted">
              © 2025 Guardian One. Advanced robotics for the modern world.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
