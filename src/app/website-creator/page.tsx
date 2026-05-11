"use client";

import Link from "next/link";
import { ArrowLeft, Paintbrush, Layers, Smartphone, Palette, ArrowRight, ExternalLink } from "lucide-react";

const features = [
  { title: "Blocs visuels", desc: "Composez votre page avec des blocs prêts à l'emploi : hero, features, FAQ, CTA.", icon: Layers },
  { title: "Responsive", desc: "Votre site s'adapte automatiquement à tous les écrans : mobile, tablette, desktop.", icon: Smartphone },
  { title: "Personnalisation", desc: "Choisissez vos couleurs, typographies et images sans toucher au code.", icon: Palette },
];

export default function WebsiteCreatorPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-50">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Retour
        </Link>

        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-4 py-1.5 text-sm text-cyan-300 mb-6">
            <Paintbrush className="h-4 w-4" /> Créateur Web
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Créez votre site en quelques clics</h1>
          <p className="mx-auto mt-4 max-w-xl text-neutral-400">
            Un constructeur de sites web pensé pour les communautés Discord. Présentez votre serveur, vos règles et vos actualités sans écrire une ligne de code.
          </p>
        </div>

        <div className="mt-14 grid gap-6 sm:grid-cols-3">
          {features.map((f) => (
            <div key={f.title} className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:-translate-y-1 hover:bg-white/[0.04]">
              <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-[#00e1ff]/10 text-[#00e1ff] ring-1 ring-white/10">
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-white">{f.title}</h3>
              <p className="mt-1 text-sm text-neutral-400">{f.desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 rounded-2xl border border-white/[0.06] bg-gradient-to-br from-[#00e1ff]/10 to-[#5865F2]/10 p-8 text-center">
          <h3 className="text-xl font-bold text-white">Prêt à créer votre page ?</h3>
          <p className="mx-auto mt-2 max-w-lg text-sm text-neutral-400">
            Le créateur web est accessible depuis votre dashboard. Connectez-vous pour commencer.
          </p>
          <div className="mt-5 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link href="/dashboard" className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#00e1ff] to-[#5865F2] px-6 py-3 text-sm font-semibold text-[#0a0a0a] shadow-lg shadow-cyan-500/20 transition-all hover:brightness-110">
              Lancer le dashboard <ArrowRight className="h-4 w-4" />
            </Link>
            <a href="https://site-cantale.vercel.app" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-6 py-3 text-sm font-semibold text-neutral-200 transition-all hover:bg-white/[0.06]">
              Voir un exemple <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
