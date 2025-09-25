import React from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { SparklesIcon } from '@heroicons/react/24/solid';

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/control', label: 'Live Control' },
  { to: '/alerts', label: 'Alerts & Logs' }
];

const Layout = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-surface via-surfaceAlt to-[#050510]">
      <div className="absolute inset-x-0 top-0 h-[30vh] bg-[radial-gradient(circle_at_top,_rgba(124,92,255,0.35),_transparent_55%)]"></div>
      <div className="absolute inset-0 -z-10 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-50 mix-blend-screen" />

      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col px-6 pb-14 pt-8 lg:px-10">
        <header className="flex flex-col gap-6 rounded-3xl bg-[#0b0d1fda] px-8 py-6 shadow-card backdrop-blur-md sm:flex-row sm:items-center sm:justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="gradient-ring flex h-12 w-12 items-center justify-center rounded-2xl bg-[#12142c]">
              <SparklesIcon className="h-7 w-7 text-accent" />
            </div>
            <div>
              <p className="text-sm uppercase tracking-[0.35em] text-muted">Robot Guardian</p>
              <h1 className="font-display text-2xl font-semibold text-foreground">Command Center</h1>
            </div>
          </Link>

          <nav className="flex items-center gap-2 rounded-full border border-white/5 bg-white/5 p-1">
            {navItems.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-full px-5 py-2 text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-accent text-white shadow-glow'
                      : 'text-muted hover:text-white hover:bg-white/10'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <main className="relative mt-10 flex-1">
          <Outlet />
        </main>

        <footer className="mt-10 flex flex-col gap-2 rounded-3xl border border-white/5 bg-white/5 px-8 py-6 text-sm text-muted backdrop-blur-md sm:flex-row sm:items-center sm:justify-between">
          <p>
            Raspberry Pi API base: <span className="text-foreground">{__PI_API__}</span>
          </p>
          <p>
            Windows Control API: <span className="text-foreground">{__WINDOWS_API__}</span>
          </p>
        </footer>
      </div>
    </div>
  );
};

export default Layout;
