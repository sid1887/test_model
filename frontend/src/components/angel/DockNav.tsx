import { Home, Search, Bell, Activity, Image as ImageIcon } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

const items = [
  { key: 'home', icon: Home, label: 'Home', path: '/' },
  { key: 'search', icon: Search, label: 'Search', path: '/search' },
  { key: 'alerts', icon: Bell, label: 'Alerts', path: '/alerts' },
  { key: 'analytics', icon: Activity, label: 'Analytics', path: '/analytics' },
  { key: 'image', icon: ImageIcon, label: 'Visual', path: '/search' },
];

export function DockNav() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="fixed z-40 bottom-6 left-1/2 -translate-x-1/2">
      <div className="backdrop-blur-xl bg-white/70 dark:bg-zinc-900/70 border border-white/30 dark:border-white/10 rounded-2xl shadow-2xl px-3 py-2 flex items-center gap-2">
        {items.map(({ key, icon: Icon, label, path }) => {
          const active = location.pathname === path || (path !== '/' && location.pathname.startsWith(path));
          return (
            <button
              key={key}
              onClick={() => navigate(path)}
              className={`group relative flex items-center gap-2 px-3 py-2 rounded-xl transition-all ${
                active ? 'bg-gradient-to-r from-fuchsia-500/20 to-sky-500/20 text-white' : 'hover:bg-white/40 dark:hover:bg-white/10'
              }`}
            >
              <Icon className={`h-5 w-5 ${active ? 'text-fuchsia-400' : 'text-zinc-600 dark:text-zinc-300'}`} />
              <span className="hidden md:block text-sm">{label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default DockNav;
