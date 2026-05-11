"use client";

import Link from "next/link";
import { ArrowLeft, Rocket, ArrowRight, Bot, Blocks, BrainCircuit, ExternalLink } from "lucide-react";

const categories = [
  {
    title: "Bots Discord",
    desc: "Vex, Asuna, Kayaba, Yui — des bots pour modérer, jouer, collectionner et animer vos serveurs.",
    icon: Bot,
    href: "/discord",
    color: "indigo",
  },
  {
    title: "Minecraft",
    desc: "Modpacks et serveurs : The French Baguette, Xenus, Vanipack et le serveur Cantale.",
    icon: Blocks,
    href: "/minecraft",
    color: "emerald",
  },
  {
    title: "Autres",
    desc: "Maths-App, cantale-site et d'autres projets communautaires liés à Synkrone.",
    icon: BrainCircuit,
    href: "/minecraft",
    color: "cyan",
    external: { label: "Maths-App", href: "https://maths-app.com" },
  },
];

export default function ProjectsPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-50">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Retour
        </Link>

        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-4 py-1.5 text-sm text-violet-300 mb-6">
            <Rocket className="h-4 w-4" /> Projets
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Nos projets</h1>
          <p className="mx-auto mt-4 max-w-xl text-neutral-400">Découvrez tous les projets développés par Synkrone et sa communauté.</p>
        </div>

        <div className="mt-14 grid gap-6 sm:grid-cols-3">
          {categories.map((c) => (
            <div key={c.title} className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:-translate-y-1 hover:bg-white/[0.04]">
              <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-${c.color}-500/10 text-${c.color}-400 ring-1 ring-white/10`}>
                <c.icon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">{c.title}</h3>
              <p className="mt-2 text-sm text-neutral-400">{c.desc}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Link href={c.href} className="inline-flex items-center gap-1.5 text-sm font-medium text-[#00e1ff] transition-colors hover:underline">
                  Voir <ArrowRight className="h-3.5 w-3.5" />
                </Link>
                {c.external && (
                  <a href={c.external.href} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-sm font-medium text-neutral-400 transition-colors hover:text-neutral-200">
                    {c.external.label} <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
