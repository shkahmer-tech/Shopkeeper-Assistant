import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Bike,
  Boxes,
  FileText,
  LayoutDashboard,
  Menu,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  ShoppingBag,
  Sun,
  TrendingUp,
  Truck,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { useTheme } from "./theme-provider";
import { Badge, useAsync } from "./ui-bits";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/inventory", label: "Inventory", icon: Boxes },
  { to: "/orders", label: "Orders", icon: ShoppingBag },
  { to: "/delivery", label: "Delivery", icon: Truck },
  { to: "/drivers", label: "Drivers", icon: Bike },
  { to: "/demand", label: "Demand", icon: TrendingUp },
  { to: "/report", label: "Full Report", icon: FileText },
];

function Logo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 512 512" fill="none" className={className} aria-hidden="true">
      <path d="M169.572 83.3331H383.899L226.326 316.888H11.9993L169.572 83.3331Z" fill="#FB0100" />
      <path
        d="M178.965 338.535L117.934 428.997H342.427L500 195.442H334.31L237.769 338.535H178.965Z"
        fill="#FF7979"
      />
    </svg>
  );
}

function SidebarBody({
  collapsed,
  onToggle,
  onNavigate,
  showToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
  onNavigate: () => void;
  showToggle: boolean;
}) {
  const { theme, toggleTheme } = useTheme();

  return (
    <>
      <div className={cn("flex h-20 shrink-0 items-center border-b", collapsed ? "justify-center" : "justify-between px-4")}>
        {collapsed ? (
          <Button aria-label="Expand sidebar" variant="secondary" size="icon" onClick={onToggle}>
            <PanelLeftOpen />
          </Button>
        ) : (
          <>
            <div className="flex items-center gap-2">
              <Logo className="size-8" />
              <span className="text-lg font-bold tracking-tight">Shopkeeper</span>
            </div>
            {showToggle && (
              <Button aria-label="Collapse sidebar" variant="secondary" size="icon" onClick={onToggle}>
                <PanelLeftClose />
              </Button>
            )}
          </>
        )}
      </div>

      <nav className="flex flex-1 flex-col gap-1.5 overflow-y-auto px-4 pt-6">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            title={collapsed ? label : undefined}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "text-muted-foreground hover:bg-muted hover:text-foreground flex h-11 items-center gap-3 rounded-lg border border-transparent px-3.5 font-medium transition-colors [&_svg]:size-5",
                collapsed && "justify-center px-0",
                isActive && "border-border bg-card text-primary hover:bg-card hover:text-primary shadow-sm",
              )
            }
          >
            <Icon />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="shrink-0 border-t px-4 py-4">
        <Button
          variant="ghost"
          className={cn("h-11 w-full justify-start gap-3 px-3.5 [&_svg]:size-5", collapsed && "justify-center px-0")}
          onClick={toggleTheme}
          title="Toggle theme"
        >
          {theme === "dark" ? <Sun /> : <Moon />}
          {!collapsed && <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>}
        </Button>
      </div>
    </>
  );
}

function Topbar({ onMenu }: { onMenu: () => void }) {
  const { pathname } = useLocation();
  const current = nav.find((n) => (n.to === "/" ? pathname === "/" : pathname.startsWith(n.to))) ?? nav[0];
  const Icon = current.icon;
  const health = useAsync(api.health);

  return (
    <header className="bg-background sticky top-0 z-30 flex h-16 items-center gap-3 border-b px-4 md:h-20 md:px-8">
      <Button variant="secondary" size="icon" className="md:hidden" aria-label="Open menu" onClick={onMenu}>
        <Menu />
      </Button>
      <div className="mr-auto flex items-center gap-3 text-lg font-medium">
        <Icon className="hidden size-5 md:block" />
        <span>{current.label}</span>
      </div>
      {health.error ? (
        <Badge tone="bad">Backend offline</Badge>
      ) : health.data ? (
        <div className="flex items-center gap-2">
          <Badge tone={health.data.demand_model_trained ? "ok" : "warn"}>
            Demand {health.data.demand_model_trained ? "ready" : "not trained"}
          </Badge>
          <Badge tone={health.data.delivery_model_trained ? "ok" : "warn"}>
            Delivery {health.data.delivery_model_trained ? "ready" : "not trained"}
          </Badge>
        </div>
      ) : null}
    </header>
  );
}

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-svh overflow-hidden">
      <aside
        className={cn(
          "bg-background hidden shrink-0 flex-col border-r transition-[width] duration-200 md:flex",
          collapsed ? "w-20" : "w-64",
        )}
      >
        <SidebarBody collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} onNavigate={() => {}} showToggle />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} />
          <aside className="bg-background absolute inset-y-0 left-0 flex w-64 flex-col border-r shadow-xl">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Close menu"
              className="absolute top-5 right-3 z-10"
              onClick={() => setMobileOpen(false)}
            >
              <X />
            </Button>
            <SidebarBody collapsed={false} onToggle={() => {}} onNavigate={() => setMobileOpen(false)} showToggle={false} />
          </aside>
        </div>
      )}

      <main className="min-w-0 flex-1 overflow-y-auto">
        <Topbar onMenu={() => setMobileOpen(true)} />
        <div className="px-5 py-6 md:px-8 md:py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
