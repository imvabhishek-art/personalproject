"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuthStore } from "@/lib/auth";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Rss,
  Wand2,
  FileText,
  Calendar,
  CreditCard,
  Settings,
  LogOut,
  ChevronDown,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/sources", label: "Sources", icon: Rss },
  { href: "/dashboard/generate", label: "Generate", icon: Wand2 },
  { href: "/dashboard/content", label: "Content", icon: FileText },
  { href: "/dashboard/schedules", label: "Schedules", icon: Calendar },
  { href: "/dashboard/credits", label: "Credits", icon: CreditCard },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, workspaces, activeWorkspace, fetchMe, fetchWorkspaces, logout, setActiveWorkspace } = useAuthStore();
  const [wsOpen, setWsOpen] = useState(false);

  useEffect(() => {
    // Demo mode: auth bypassed
  }, []);

  const handleLogout = () => {
    logout();
    router.push("/auth/login");
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-zinc-200 flex flex-col shrink-0">
        <div className="p-4 border-b border-zinc-100">
          <h1 className="font-bold text-zinc-900 text-sm">Newsletter Agent</h1>
        </div>

        {/* Workspace switcher */}
        <div className="p-2 border-b border-zinc-100 relative">
          <button
            onClick={() => setWsOpen((v) => !v)}
            className="w-full flex items-center justify-between px-2 py-1.5 rounded-md hover:bg-zinc-50 text-sm"
          >
            <span className="font-medium text-zinc-800 truncate">
              {activeWorkspace?.name || "No workspace"}
            </span>
            <ChevronDown className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
          </button>
          {wsOpen && workspaces.length > 0 && (
            <div className="absolute top-full left-2 right-2 bg-white border border-zinc-200 rounded-md shadow-md z-10">
              {workspaces.map((ws) => (
                <button
                  key={ws.id}
                  onClick={() => { setActiveWorkspace(ws); setWsOpen(false); }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-zinc-50 flex items-center gap-2"
                >
                  <span className={cn("truncate", activeWorkspace?.id === ws.id && "font-medium")}>
                    {ws.name}
                  </span>
                </button>
              ))}
              <div className="border-t border-zinc-100 p-1">
                <Link
                  href="/onboarding"
                  className="block px-3 py-1.5 text-xs text-zinc-500 hover:text-zinc-800 hover:bg-zinc-50 rounded"
                  onClick={() => setWsOpen(false)}
                >
                  + New workspace
                </Link>
              </div>
            </div>
          )}
        </div>

        <nav className="flex-1 p-2 space-y-0.5">
          {NAV.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2.5 px-2 py-1.5 rounded-md text-sm transition-colors",
                pathname === href
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          ))}
        </nav>

        <div className="p-2 border-t border-zinc-100">
          <div className="px-2 py-1.5 text-xs text-zinc-400 truncate">{user?.email}</div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-2 py-1.5 rounded-md text-sm text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto bg-zinc-50">
        {children}
      </main>
    </div>
  );
}
