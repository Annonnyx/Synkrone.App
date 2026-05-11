"use client";

import Link from "next/link";
import { ArrowLeft, Users, Cpu, Server, ArrowRight, ExternalLink } from "lucide-react";

const members = [
  { name: "Vex", role: "Lead dev — Architecture logicielle et bots Discord", color: "indigo", icon: Cpu, github: "https://github.com/vex" },
  { name: "Ønyx", role: "Infrastructure & cloud — Stabilité des systèmes", color: "emerald", icon: Server, github: "https://github.com/Annonnyx" },
];

const jobs = [
  { title: "Développeur Frontend", desc: "Rejoins l'équipe pour améliorer l'expérience utilisateur de Synkrone." },
  { title: "Community Manager", desc: "Anime notre communauté Discord et fais rayonner Synkrone." },
  { title: "Modérateur", desc: "Maintiens un environnement sain sur nos serveurs de support." },
];

export default function TeamPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-50">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Retour
        </Link>

        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-4 py-1.5 text-sm text-amber-300 mb-6">
            <Users className="h-4 w-4" /> L&apos;équipe
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Les architectes de Synkrone</h1>
          <p className="mx-auto mt-4 max-w-xl text-neutral-400">Une petite équipe passionnée qui construit des outils puissants pour les communautés Discord.</p>
        </div>

        <div className="mt-14 grid gap-8 sm:grid-cols-2 max-w-3xl mx-auto">
          {members.map((m) => (
            <div key={m.name} className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8 transition-all hover:-translate-y-1 hover:bg-white/[0.04]">
              <div className={`mb-5 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-${m.color}-500/10 text-${m.color}-400 ring-1 ring-white/10`}>
                <m.icon className="h-7 w-7" />
              </div>
              <h3 className="text-xl font-bold text-white">{m.name}</h3>
              <p className="mt-1 text-sm font-medium text-neutral-400">{m.role}</p>
              <a href={m.github} target="_blank" rel="noopener noreferrer" className="mt-4 inline-flex items-center gap-1.5 text-sm text-[#00e1ff] hover:underline">
                <ExternalLink className="h-3.5 w-3.5" /> GitHub
              </a>
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold text-white">On recrute !</h2>
          <p className="mt-2 text-neutral-400">Tous les profils sont les bienvenus.</p>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          {jobs.map((j) => (
            <div key={j.title} className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:bg-white/[0.04]">
              <h3 className="font-semibold text-white">{j.title}</h3>
              <p className="mt-1 text-sm text-neutral-400">{j.desc}</p>
              <a href="https://discord.gg/nuFNvVybGE" target="_blank" rel="noopener noreferrer" className="mt-4 inline-flex items-center gap-1.5 text-sm text-[#00e1ff] hover:underline">
                Postuler <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm text-neutral-500">Même sans poste ouvert, on est toujours curieux de rencontrer des gens passionnés.</p>
          <a href="mailto:contact@synkrone.fr" className="mt-3 inline-flex items-center gap-2 text-sm text-[#00e1ff] hover:underline">
            Nous contacter
          </a>
        </div>
      </div>
    </div>
  );
}
