"use client";

import Link from "next/link";
import { useSession } from "next-auth/react";
import { Menu, X } from "lucide-react";
import { useState } from "react";

export function Navbar() {
  const { status } = useSession();
  const isLoggedIn = status === "authenticated";
  const [menuOpen, setMenuOpen] = useState(false);

  const links = [
    { href: "/projects", label: "Projets" },
    { href: "/minecraft", label: "Minecraft" },
    { href: "/discord", label: "Discord" },
    { href: "/pricing", label: "Krônes" },
    { href: "/team", label: "Équipe" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/[0.04] bg-[#0a0a0a]/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5">
        <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-tight text-white">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-[#00e1ff] to-[#5865F2]" />
          Synkrone
        </Link>

        {/* Desktop links */}
        <div className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <a key={l.href} href={l.href} className="text-sm font-medium text-neutral-400 transition-colors hover:text-white">
              {l.label}
            </a>
          ))}
        </div>

        <div className="hidden md:block">
          {isLoggedIn ? (
            <Link
              href="/dashboard"
              className="rounded-lg bg-white/[0.06] px-4 py-2 text-sm font-medium text-white ring-1 ring-white/10 transition-colors hover:bg-white/[0.1]"
            >
              Dashboard
            </Link>
          ) : (
            <Link
              href="/login"
              className="rounded-lg bg-gradient-to-r from-[#00e1ff] to-[#5865F2] px-4 py-2 text-sm font-semibold text-[#0a0a0a] shadow-lg shadow-cyan-500/20 transition-all hover:brightness-110"
            >
              Se connecter
            </Link>
          )}
        </div>

        {/* Mobile menu toggle */}
        <button className="md:hidden text-neutral-300" onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="border-t border-white/[0.04] bg-[#0a0a0a]/95 px-6 py-4 md:hidden">
          <div className="flex flex-col gap-4">
            {links.map((l) => (
              <a key={l.href} href={l.href} className="text-sm font-medium text-neutral-400 hover:text-white" onClick={() => setMenuOpen(false)}>
                {l.label}
              </a>
            ))}
            {isLoggedIn ? (
              <Link href="/dashboard" className="rounded-lg bg-white/[0.06] px-4 py-2 text-center text-sm font-medium text-white" onClick={() => setMenuOpen(false)}>
                Dashboard
              </Link>
            ) : (
              <Link href="/login" className="rounded-lg bg-gradient-to-r from-[#00e1ff] to-[#5865F2] px-4 py-2 text-center text-sm font-semibold text-[#0a0a0a] shadow-lg shadow-cyan-500/20" onClick={() => setMenuOpen(false)}>
                Se connecter
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
