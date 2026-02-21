import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: "\u2302" },
  { to: "/bootstrap", label: "Bootstrap", icon: "\u26A1" },
  { to: "/api-foundation", label: "API Foundation", icon: "\u{1F310}" },
  { to: "/milestones", label: "Milestones", icon: "\u{1F3AF}" },
  { to: "/companion", label: "Companion", icon: "\u{1F916}" },
  { to: "/database", label: "Database", icon: "\u{1F4BE}" },
  { to: "/auth", label: "Auth", icon: "\u{1F512}" },
];

export function SideNav() {
  return (
    <nav className="w-52 min-h-full bg-cosmic-card border-r border-cosmic-border flex flex-col py-4 gap-1 shrink-0">
      {navItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === "/"}
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors rounded-r-lg mr-2 ${
              isActive
                ? "bg-cosmic-primary-accent/10 text-cosmic-primary-accent border-l-2 border-cosmic-primary-accent"
                : "text-cosmic-text-secondary hover:text-cosmic-text-primary hover:bg-white/5"
            }`
          }
        >
          <span className="text-base">{item.icon}</span>
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
