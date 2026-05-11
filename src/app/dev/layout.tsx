"use client";

import { useSession } from "next-auth/react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { hasRole } from "@/lib/roles";

const baseLinks = [
  { href: "/dev", label: "Vue d'ensemble", icon: OverviewIcon },
  { href: "/dev/boxes", label: "Ma Box", icon: BoxIcon },
  { href: "/dev/boxes/shared", label: "Box Partagée", icon: SharedIcon },
];

function OverviewIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
    </svg>
  );
}

function BoxIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
    </svg>
  );
}

function SharedIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7.217 10.907a2.25 2.25 0 1 0 0 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186 9.566-5.314m-9.566 7.5 9.566 5.314m0 0a2.25 2.25 0 1 0 3.935 2.186 2.25 2.25 0 0 0-3.935-2.186Zm0-12.814a2.25 2.25 0 1 0 3.933-2.185 2.25 2.25 0 0 0-3.933 2.185Z" />
    </svg>
  );
}

function UsersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.295-2.228-.861-3.22a12.044 12.044 0 0 0-4.989-4.56A12.003 12.003 0 0 0 3.75 12.75c0 .649.045 1.29.134 1.916M15 19.128a5.632 5.632 0 0 1-5.14-3.345 5.634 5.634 0 0 1-1.273-3.595c0-2.03.765-3.875 2.014-5.284M15 19.128c1.755-.598 3.135-2.085 3.728-3.977M12 15.75h.008v.008H12v-.008Z" />
    </svg>
  );
}

function BotIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-1.5a2.25 2.25 0 00-2.25-2.25H4.5a2.25 2.25 0 00-2.25 2.25v1.5a2.25 2.25 0 002.25 2.25z" />
    </svg>
  );
}

function BoxesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25a2.25 2.25 0 0 1-2.25 2.25H15.75a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25a2.25 2.25 0 0 1-2.25-2.25v-2.25Z" />
    </svg>
  );
}

function TerminalIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m6.75 7.5 3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0 0 21 18V6a2.25 2.25 0 0 0-2.25-2.25H5.25A2.25 2.25 0 0 0 3 6v12a2.25 2.25 0 0 0 2.25 2.25Z" />
    </svg>
  );
}

export default function DevLayout({ children }: { children: React.ReactNode }) {
  const { data: session } = useSession();
  const pathname = usePathname();
  const user = session?.user;
  const roles = user?.roles ?? [];

  const isManagerOrAbove = hasRole(roles, "MANAGER");
  const isSupervisorOrAbove = hasRole(roles, "SUPERVISOR");
  const isLeader = hasRole(roles, "LEADER");

  const adminLinks: { href: string; label: string; icon: typeof OverviewIcon }[] = [];
  if (isManagerOrAbove) {
    adminLinks.push(
      { href: "/dev/admin/users", label: "Utilisateurs", icon: UsersIcon },
      { href: "/dev/admin/bots", label: "Tous les Bots", icon: BotIcon }
    );
  }
  if (isSupervisorOrAbove) {
    adminLinks.push({ href: "/dev/admin/boxes", label: "Toutes les Boxes", icon: BoxesIcon });
  }
  if (isLeader) {
    adminLinks.push({ href: "/dev/admin/terminal", label: "Terminal VPS", icon: TerminalIcon });
  }

  const navLinks = [...baseLinks, ...(adminLinks.length > 0 ? [{ href: "", label: "Administration", icon: () => null, isHeader: true as const }, ...adminLinks] : [])];

  return (
    <div className="flex min-h-screen bg-neutral-950 text-neutral-50">
      {/* SIDEBAR */}
      <aside className="fixed left-0 top-0 h-screen w-60 border-r border-neutral-800 bg-neutral-900 flex flex-col">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-neutral-800">
          <Link href="/dev" className="text-xl font-bold tracking-tight text-cyan-400">
            Synkrone<span className="text-neutral-400">.dev</span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navLinks.map((link, idx) => {
            if ("isHeader" in link) {
              return (
                <div key={`header-${idx}`} className="mt-4 mb-1 px-3 text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                  {link.label}
                </div>
              );
            }
            const isActive = pathname === link.href || (link.href && pathname.startsWith(link.href + "/"));
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-neutral-800 text-cyan-400"
                    : "text-neutral-400 hover:bg-neutral-800 hover:text-white"
                }`}
              >
                <Icon className="h-5 w-5 shrink-0" />
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Retour */}
        <div className="border-t border-neutral-800 px-4 py-4">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-neutral-400 transition-colors hover:bg-neutral-800 hover:text-white"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
            </svg>
            ← Retour App
          </Link>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="ml-60 flex-1 min-h-screen">
        {children}
      </main>
    </div>
  );
}
