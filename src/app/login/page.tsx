"use client";

import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import Link from "next/link";
import { ArrowLeft, Sparkles, Shield, Zap, Globe } from "lucide-react";

function LoginContent() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/dashboard";

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#0a0a0a] text-neutral-50">
      {/* Background effects */}
      <div className="absolute inset-0 grid-bg opacity-40" />
      <div className="absolute top-1/4 -left-32 h-96 w-96 rounded-full bg-[#00e1ff]/10 blur-[120px] animate-pulse-glow" />
      <div className="absolute bottom-1/4 -right-32 h-96 w-96 rounded-full bg-[#5865F2]/10 blur-[120px] animate-pulse-glow" style={{ animationDelay: "2s" }} />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-6xl items-center justify-center px-6">
        <div className="grid w-full gap-12 lg:grid-cols-2 lg:gap-20">
          {/* Left — branding & features */}
          <div className="flex flex-col justify-center">
            <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white">
              <ArrowLeft className="h-4 w-4" />
              Retour à l&apos;accueil
            </Link>

            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#00e1ff]/20 bg-[#00e1ff]/5 px-4 py-1.5 text-sm text-cyan-accent w-fit">
              <Sparkles className="h-4 w-4" />
              Synkrone
            </div>

            <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl leading-[1.1]">
              Bienvenue sur{" "}
              <span className="bg-gradient-to-r from-[#00e1ff] to-[#5865F2] bg-clip-text text-transparent">
                Synkrone
              </span>
            </h1>
            <p className="mt-4 max-w-md text-lg text-neutral-400">
              Créez votre bot Discord, hébergez votre serveur Minecraft et gérez vos projets depuis un dashboard unifié.
            </p>

            <div className="mt-8 space-y-4">
              {[
                { icon: Zap, text: "Créez un bot sans code en minutes" },
                { icon: Shield, text: "Hébergement cloud inclus et sécurisé" },
                { icon: Globe, text: "Dashboard intuitif et analytics temps réel" },
              ].map((f) => (
                <div key={f.text} className="flex items-center gap-3 text-sm text-neutral-400">
                  <div className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-[#00e1ff]/10 text-[#00e1ff]">
                    <f.icon className="h-4 w-4" />
                  </div>
                  {f.text}
                </div>
              ))}
            </div>
          </div>

          {/* Right — login card */}
          <div className="flex items-center justify-center">
            <div className="w-full max-w-sm rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8 backdrop-blur-sm shadow-2xl hover-glow transition-all duration-500">
              <div className="flex flex-col items-center gap-2">
                <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-[#00e1ff] to-[#5865F2] shadow-lg shadow-cyan-500/20" />
                <h2 className="text-xl font-bold text-white">Connexion</h2>
                <p className="text-sm text-neutral-400">Continuez avec Discord pour accéder à votre dashboard.</p>
              </div>

              <button
                onClick={() => signIn("discord", { callbackUrl })}
                className="btn-click pulse-ring mt-6 flex w-full items-center justify-center gap-3 rounded-xl bg-[#5865F2] px-6 py-3.5 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 transition-all hover:bg-[#4752c4]"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057.102 18.079.114 18.1.132 18.11a19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z"/>
                </svg>
                Se connecter avec Discord
              </button>

              <div className="mt-5 flex items-center gap-3">
                <div className="h-px flex-1 bg-white/[0.06]" />
                <span className="text-xs text-neutral-500">ou</span>
                <div className="h-px flex-1 bg-white/[0.06]" />
              </div>

              <Link
                href="/"
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-6 py-3 text-sm font-semibold text-neutral-200 transition-all hover:bg-white/[0.06]"
              >
                Explorer le site
              </Link>

              <p className="mt-6 text-center text-xs leading-relaxed text-neutral-500">
                En vous connectant, vous acceptez nos{" "}
                <Link href="/legal/terms" className="text-[#00e1ff] hover:underline">CGU</Link>
                {" "}et notre{" "}
                <Link href="/legal/privacy" className="text-[#00e1ff] hover:underline">politique de confidentialité</Link>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginContent />
    </Suspense>
  );
}
