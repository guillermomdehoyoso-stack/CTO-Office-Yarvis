import { NavLink } from 'react-router-dom';

export interface NavEntry {
  path: string;
  label: string;
}

export function SidebarNav({ entries }: { entries: NavEntry[] }) {
  return (
    <aside className="sidebar">
      <h2>Yarvis</h2>
      <p>Workspace Platform</p>
      <nav>
        {entries.map((entry) => (
          <NavLink
            key={entry.path}
            className={({ isActive }) => (isActive ? 'active-nav' : '')}
            to={entry.path}
          >
            {entry.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
