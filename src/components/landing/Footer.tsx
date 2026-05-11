"use client";

import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-white/[0.04] bg-[#0a0a0a]">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="flex flex-col gap-3">
            <Link href="/" className="flex items-center gap-2 text-lg font-bold text-white">
              <div className="h-6 w-6 rounded-md bg-gradient-to-br from-[#00e1ff] to-[#5865F2]" />
              Synkrone
            </Link>
            <p className="text-sm leading-relaxed text-neutral-500">
              Créez votre bot Discord personnalisé en quelques clics avec des modules prêts à l&apos;emploi.
            </p>
          </div>

          {/* Produit */}
          <div>
            <h4 className="text-sm font-semibold text-white">Produit</h4>
            <ul className="mt-4 space-y-2.5">
              {[
                { label: "Dashboard", href: "/dashboard" },
                { label: "Créateur Web", href: "/website-creator" },
                { label: "Krônes", href: "/pricing" },
                { label: "Modules", href: "/dashboard" },
              ].map((item) => (
                <li key={item.label}>
                  <Link href={item.href} className="text-sm text-neutral-500 transition-colors hover:text-neutral-300">
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Communauté */}
          <div>
            <h4 className="text-sm font-semibold text-white">Communauté</h4>
            <ul className="mt-4 space-y-2.5">
              {[
                { label: "Discord Support", href: "https://discord.gg/nuFNvVybGE", external: true },
                { label: "Nos bots Discord", href: "/discord", external: false },
                { label: "Minecraft", href: "/minecraft", external: false },
                { label: "The French Baguette", href: "https://discord.gg/jX9mFnEk72", external: true },
                { label: "Maths-App", href: "https://maths-app.com", external: true },
              ].map((item) => (
                <li key={item.label}>
                  {item.external ? (
                    <a href={item.href} target="_blank" rel="noopener noreferrer" className="text-sm text-neutral-500 transition-colors hover:text-neutral-300">
                      {item.label}
                    </a>
                  ) : (
                    <Link href={item.href} className="text-sm text-neutral-500 transition-colors hover:text-neutral-300">
                      {item.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Légal */}
          <div>
            <h4 className="text-sm font-semibold text-white">Légal</h4>
            <ul className="mt-4 space-y-2.5">
              {[
                { label: "CGU", href: "/legal/terms" },
                { label: "Confidentialité", href: "/legal/privacy" },
                { label: "Mentions légales", href: "/legal/notices" },
              ].map((item) => (
                <li key={item.label}>
                  <Link href={item.href} className="text-sm text-neutral-500 transition-colors hover:text-neutral-300">
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-white/[0.04] pt-8 sm:flex-row">
          <p className="text-xs text-neutral-600">© 2026 Synkrone. Tous droits réservés.</p>
          <div className="flex gap-4">
            <a href="https://discord.gg/nuFNvVybGE" target="_blank" rel="noopener noreferrer" className="text-xs text-neutral-600 hover:text-neutral-400">Discord</a>
            <a href="https://synkrone.app" target="_blank" rel="noopener noreferrer" className="text-xs text-neutral-600 hover:text-neutral-400">Synkrone.app</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
