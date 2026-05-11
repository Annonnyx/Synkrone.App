"use client";

import Link from "next/link";
import {
  Blocks,
  ArrowLeft,
  BookOpen,
  Cloud,
  TreePine,
  Globe,
  ExternalLink,
  ArrowRight,
} from "lucide-react";

const modpacks = [
  {
    name: "The French Baguette",
    desc: "Modpack pensé pour la communauté francophone. Il combine des mods de technologie et d'aventure avec un livre de quête complet en français pour guider les joueurs.",
    type: "Technologie + Aventure",
    lang: "Français",
    version: "1.20.1",
    launcher: "CurseForge / Modrinth",
    color: "emerald",
    icon: BookOpen,
    features: ["Livre de quête en français", "Mods de technologie", "Mods d'aventure"],
  },
  {
    name: "Xenus",
    desc: "Modpack Skyblock unique qui repousse les limites de la progression technologique. Partez d'une île flottante et développez votre empire grâce à des mods avancés.",
    type: "Skyblock",
    lang: "Français",
    version: "1.20.1",
    difficulty: "Avancé",
    color: "sky",
    icon: Cloud,
    features: ["Livre de quête en français", "Gameplay Skyblock unique", "Mods technologiques avancés"],
  },
  {
    name: "Vanipack",
    desc: "Expérience vanilla améliorée sans dénaturer le jeu d'origine. Léger et accessible, compatible avec les serveurs non moddés.",
    type: "Vanilla+",
    lang: "Français",
    version: "1.20.1",
    weight: "Léger",
    color: "amber",
    icon: TreePine,
    features: ["Expérience vanilla améliorée", "Léger et accessible", "Compatible serveurs non moddés"],
  },
];

const serverProject = {
  name: "Cantale",
  desc: "Serveur Minecraft avec son propre site officiel. Rejoignez une communauté active, inscrivez-vous en ligne et découvrez un serveur unique avec des fonctionnalités exclusives.",
  type: "Serveur + Site web",
  site: "site-cantale.vercel.app",
  access: "Inscription en ligne",
  color: "rose",
  icon: Globe,
  features: ["Serveur Minecraft", "Site officiel", "Communauté active"],
};

export default function MinecraftPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-50">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white">
          <ArrowLeft className="h-4 w-4" />
          Retour à l&apos;accueil
        </Link>

        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-4 py-1.5 text-sm text-emerald-300 mb-6">
            <Blocks className="h-4 w-4" />
            Projets Minecraft
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Modpacks & Serveurs
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-neutral-400">
            Découvrez nos modpacks et projets Minecraft. Des expériences variées, fun et accessibles à tous !
          </p>
        </div>

        {/* Modpacks */}
        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {modpacks.map((pack) => (
            <div
              key={pack.name}
              className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:-translate-y-1 hover:bg-white/[0.04]"
            >
              <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-${pack.color}-500/10 text-${pack.color}-400 ring-1 ring-white/10`}>
                <pack.icon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">{pack.name}</h3>
              <p className="mt-2 text-sm leading-relaxed text-neutral-400">{pack.desc}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-md bg-white/[0.04] px-2 py-0.5 text-xs text-neutral-400 ring-1 ring-white/[0.06]">{pack.type}</span>
                <span className="rounded-md bg-white/[0.04] px-2 py-0.5 text-xs text-neutral-400 ring-1 ring-white/[0.06]">{pack.lang}</span>
                <span className="rounded-md bg-white/[0.04] px-2 py-0.5 text-xs text-neutral-400 ring-1 ring-white/[0.06]">{pack.version}</span>
                {pack.launcher && <span className="rounded-md bg-white/[0.04] px-2 py-0.5 text-xs text-neutral-400 ring-1 ring-white/[0.06]">{pack.launcher}</span>}
                {pack.difficulty && <span className="rounded-md bg-white/[0.04] px-2 py-0.5 text-xs text-neutral-400 ring-1 ring-white/[0.06]">{pack.difficulty}</span>}
                {pack.weight && <span className="rounded-md bg-white/[0.04] px-2 py-0.5 text-xs text-neutral-400 ring-1 ring-white/[0.06]">{pack.weight}</span>}
              </div>
              <ul className="mt-4 space-y-1">
                {pack.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-xs text-neutral-400">
                    <span className="h-1 w-1 rounded-full bg-emerald-400" />{f}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Server project */}
        <div className="mt-8">
          <div className="mx-auto max-w-md rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:-translate-y-1 hover:bg-white/[0.04]">
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-rose-500/10 text-rose-400 ring-1 ring-white/10">
              <Globe className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold text-white">{serverProject.name}</h3>
            <p className="mt-2 text-sm leading-relaxed text-neutral-400">{serverProject.desc}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="rounded-md bg-white/[0.04] px-2 py-0.5 text-xs text-neutral-400 ring-1 ring-white/[0.06]">{serverProject.type}</span>
              <span className="rounded-md bg-white/[0.04] px-2 py-0.5 text-xs text-neutral-400 ring-1 ring-white/[0.06]">{serverProject.access}</span>
            </div>
            <ul className="mt-4 space-y-1">
              {serverProject.features.map((f) => (
                <li key={f} className="flex items-center gap-2 text-xs text-neutral-400">
                  <span className="h-1 w-1 rounded-full bg-emerald-400" />{f}
                </li>
              ))}
            </ul>
            <a
              href="https://site-cantale.vercel.app"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-5 inline-flex items-center gap-2 rounded-xl bg-rose-600 px-5 py-2.5 text-sm font-semibold text-white transition-all hover:bg-rose-500"
            >
              Visiter Cantale <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-14 text-center">
          <p className="text-neutral-400">Téléchargez nos modpacks et rejoignez la communauté Synkrone.</p>
          <div className="mt-4 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <a
              href="https://discord.gg/p768u2Pgp3"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#00e1ff] to-[#5865F2] px-6 py-3 text-sm font-semibold text-[#0a0a0a] shadow-lg shadow-cyan-500/20 transition-all hover:brightness-110"
            >
              Discord Support <ArrowRight className="h-4 w-4" />
            </a>
            <a
              href="https://site-cantale.vercel.app"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-6 py-3 text-sm font-semibold text-neutral-200 transition-all hover:bg-white/[0.06]"
            >
              Cantale <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
