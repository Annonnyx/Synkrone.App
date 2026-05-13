"use client";

import { useSession } from "next-auth/react";
import Link from "next/link";
import {
  Bot,
  Blocks,
  Globe,
  Smartphone,
  ArrowRight,
  Zap,
  Shield,
  Sparkles,
  Users,
  Server,
  CreditCard,
  Dices,
  Wrench,
  Layers,
  ExternalLink,
  BrainCircuit,
  Cpu,
  BookOpen,
  Cloud,
  TreePine,
} from "lucide-react";
import { Navbar } from "@/components/landing/Navbar";
import { GradientOrb } from "@/components/landing/GradientOrb";
import { FeatureCard } from "@/components/landing/FeatureCard";
import { StepItem } from "@/components/landing/StepItem";
import PricingBuilder from "@/components/landing/PricingBuilder";
import { Footer } from "@/components/landing/Footer";

const stats = [
  { value: "1 200+", label: "Utilisateurs" },
  { value: "850+", label: "Bots créés" },
  { value: "320+", label: "Serveurs Minecraft" },
  { value: "99.9%", label: "Uptime" },
];

const features = [
  {
    icon: Bot,
    title: "Bot Discord",
    description: "Créez un bot personnalisé avec vos commandes favorites. Déployé en quelques minutes, sans code.",
  },
  {
    icon: Blocks,
    title: "Serveur Minecraft",
    description: "Hébergez votre serveur avec toutes les versions supportées. RAM scalable à la demande.",
  },
  {
    icon: Globe,
    title: "Site Web",
    description: "Demandez la création de votre site vitrine, portfolio ou e-commerce. Hébergement inclus.",
  },
  {
    icon: Smartphone,
    title: "Application",
    description: "Faites développer et héberger votre application web ou bot sur mesure par notre équipe.",
  },
];

const steps = [
  {
    icon: CreditCard,
    title: "Créez votre compte",
    description: "Connectez-vous en 2 clics via Discord. Recevez 1 000 Krônes de bienvenue.",
  },
  {
    icon: Sparkles,
    title: "Choisissez votre service",
    description: "Sélectionnez un bot, un serveur Minecraft, un site ou une app parmi nos offres.",
  },
  {
    icon: Zap,
    title: "Déployez en live",
    description: "Votre service est actif en moins d'une minute. Gérez-le depuis votre dashboard.",
  },
];


export default function Home() {
  const { status } = useSession();
  const isLoggedIn = status === "authenticated";

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-50 overflow-x-hidden">
      <Navbar />

      {/* HERO */}
      <section className="relative flex flex-col items-center px-6 pt-36 pb-24 text-center">
        {/* Background effects */}
        <div className="absolute inset-0 grid-bg opacity-50 pointer-events-none" />
        <GradientOrb className="top-20 left-1/4 h-96 w-96 bg-[#00e1ff]" delay={0} />
        <GradientOrb className="top-32 right-1/4 h-80 w-80 bg-[#5865F2]" delay={2} />
        <GradientOrb className="bottom-0 left-1/3 h-72 w-72 bg-[#a855f7]" delay={4} />

        <div className="relative z-10 mx-auto max-w-5xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#00e1ff]/20 bg-[#00e1ff]/5 px-4 py-1.5 text-sm text-cyan-accent backdrop-blur-sm mb-8">
            <Sparkles className="h-4 w-4 text-[#00e1ff]" />
            Créez votre bot Discord gratuitement
          </div>

          <h1 className="text-5xl font-extrabold tracking-tight text-white sm:text-6xl md:text-7xl leading-[1.1]">
            Créez votre{" "}
            <span className="bg-gradient-to-r from-[#00e1ff] via-[#5865F2] to-[#a855f7] bg-clip-text text-transparent">
              bot sans code
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-neutral-400">
            Modules pré-codés, hébergement flexible, analytics temps réel.
          </p>

          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
            <Link
              href={isLoggedIn ? "/dashboard" : "/login"}
              className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#00e1ff] to-[#5865F2] px-8 py-3.5 text-base font-semibold text-[#0a0a0a] shadow-lg shadow-cyan-500/20 transition-all hover:brightness-110 hover:scale-[1.02]"
            >
              {isLoggedIn ? "Lancer le dashboard" : "Commencer gratuitement"}
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <a
              href="#pricing"
              className="inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-8 py-3.5 text-base font-semibold text-neutral-200 backdrop-blur-sm transition-all hover:bg-white/[0.06]"
            >
              Voir les Krônes
            </a>
          </div>
        </div>
      </section>

      {/* STATS */}
      <section className="relative border-y border-white/[0.04] bg-white/[0.01]">
        <div className="mx-auto max-w-7xl px-6 py-12">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {stats.map((s, i) => (
              <div key={i} className="flex flex-col items-center text-center">
                <span className="text-3xl font-extrabold text-white">{s.value}</span>
                <span className="mt-1 text-sm text-neutral-500">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TOUT INCLUS */}
      <section id="services" className="mx-auto max-w-7xl px-6 py-24">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Tout inclus
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-neutral-400">
            Tout ce dont vous avez besoin pour créer et héberger votre bot Discord.
          </p>
        </div>
        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {[
            {
              icon: Bot,
              title: "Modules pré-codés",
              desc: "Auto-rôles, modération, économie, musique. Activez ce dont vous avez besoin.",
              color: "cyan",
            },
            {
              icon: Sparkles,
              title: "Zéro code",
              desc: "Configuration visuelle. Votre bot en ligne en minutes.",
              color: "violet",
            },
            {
              icon: Cloud,
              title: "Cloud ou Self-hosted",
              desc: "Hébergement Synkrone ou code source complet pour auto-hébergement.",
              color: "emerald",
            },
            {
              icon: CreditCard,
              title: "Paiement flexible",
              desc: "Payez ce que vous utilisez. Pas d'abonnement forcé.",
              color: "amber",
            },
            {
              icon: Globe,
              title: "Site web inclus",
              desc: "Créez une page pour votre serveur avec notre constructeur.",
              color: "indigo",
            },
          ].map((f, i) => (
            <div
              key={f.title}
              className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:-translate-y-1 hover:bg-white/[0.04]"
            >
              <div className={`mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-${f.color}-500/10 text-${f.color}-400 ring-1 ring-white/10`}>
                <f.icon className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-white">{f.title}</h3>
              <p className="mt-1 text-sm text-neutral-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works" className="relative border-y border-white/[0.04] bg-white/[0.01]">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Comment ça marche ?
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-neutral-400">
              Trois étapes simples pour déployer votre premier service.
            </p>
          </div>
          <div className="mt-14 grid gap-10 sm:grid-cols-3">
            {steps.map((s, i) => (
              <StepItem key={s.title} step={i + 1} {...s} />
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="relative border-y border-white/[0.04] bg-white/[0.01]">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#00e1ff]/20 bg-[#00e1ff]/5 px-4 py-1.5 text-sm text-cyan-accent mb-6">
              <Sparkles className="h-4 w-4 text-[#00e1ff]" />
              Tarification flexible
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Composez votre offre
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-neutral-400">
              Sélectionnez exactement ce dont vous avez besoin. Plus vous prenez de services, plus vous économisez.
            </p>
          </div>
          <div className="mt-14">
            <PricingBuilder />
          </div>
        </div>
      </section>

      {/* MINECRAFT */}
      <section id="minecraft" className="relative border-y border-white/[0.04] bg-white/[0.01]">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-4 py-1.5 text-sm text-emerald-300 mb-6">
              <Blocks className="h-4 w-4" />
              Modpacks communautaires
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Minecraft Modpacks
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-neutral-400">
              Découvrez notre sélection de modpacks pensés pour la communauté Synkrone. Des expériences variées, fun et accessibles à tous !
            </p>
          </div>
          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                name: "The French Baguette",
                desc: "Livre de quête en français. Mods de technologie et d'aventure pour une progression guidée.",
                color: "emerald",
                icon: BookOpen,
              },
              {
                name: "Xenus",
                desc: "Gameplay Skyblock unique avec livre de quête en français. Mods technologiques avancés.",
                color: "sky",
                icon: Cloud,
              },
              {
                name: "Vanipack",
                desc: "Expérience vanilla améliorée. Jouable même sur des serveurs non moddés.",
                color: "amber",
                icon: TreePine,
              },
            ].map((pack) => (
              <div
                key={pack.name}
                className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:-translate-y-1 hover:bg-white/[0.04]"
              >
                <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-${pack.color}-500/10 text-${pack.color}-400 ring-1 ring-white/10`}>
                  <pack.icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold text-white">{pack.name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-neutral-400">{pack.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* DISCORD BOTS */}
      <section id="discord" className="mx-auto max-w-7xl px-6 py-24">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-4 py-1.5 text-sm text-indigo-300 mb-6">
            <Bot className="h-4 w-4" />
            Prêts à l&apos;emploi
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Nos bots Discord
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-neutral-400">
            Une suite de bots pensée pour enrichir vos serveurs. Modération, casino, collection et utilitaires.
          </p>
        </div>
        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              name: "Vex",
              slug: "vex",
              tag: "Multifonction",
              desc: "Le bot principal de Synkrone. Modération, utilitaires, économie et plus encore.",
              color: "indigo",
              icon: Bot,
              invite: "https://discord.com/oauth2/authorize?client_id=1368234765638963261",
              support: "https://discord.gg/p768u2Pgp3",
              vote: "https://top.gg/fr/bot/1367891720871874560",
            },
            {
              name: "Asuna",
              slug: "asuna",
              tag: "Modération",
              desc: "Gestion complète de votre serveur. Création de salons et rôles, modération avancée, purge et backup.",
              color: "cyan",
              icon: Wrench,
              invite: "https://discord.com/oauth2/authorize?client_id=1428865683986452640",
              support: "https://discord.gg/p768u2Pgp3",
            },
            {
              name: "Kayaba",
              slug: "kayaba",
              tag: "Utilitaires",
              desc: "Collection de cartes, marché communautaire, échanges sécurisés et duels tour par tour.",
              color: "amber",
              icon: Layers,
              invite: "https://discord.com/oauth2/authorize?client_id=1385913159717621780",
              support: "https://discord.gg/p768u2Pgp3",
            },
            {
              name: "Yui",
              slug: "yui",
              tag: "Fun & Jeux",
              desc: "Casino complet : machine à sous, mines, blackjack, roulette, coffres scellés et pièce double ou rien.",
              color: "rose",
              icon: Dices,
              invite: "https://discord.com/oauth2/authorize?client_id=1460012999912853810",
              support: "https://discord.gg/p768u2Pgp3",
            },
          ].map((bot) => (
            <div
              key={bot.name}
              className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:-translate-y-1 hover:bg-white/[0.04]"
            >
              <div className={`absolute top-4 right-4 rounded-md bg-${bot.color}-500/20 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-${bot.color}-300`}>
                {bot.tag}
              </div>
              <div className={`mb-4 mt-6 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-${bot.color}-500/10 text-${bot.color}-400 ring-1 ring-white/10`}>
                <bot.icon className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">{bot.name}</h3>
              <p className="mt-2 text-sm leading-relaxed text-neutral-400">{bot.desc}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <a
                  href={bot.invite}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-[#5865F2] px-3 py-1.5 text-xs font-semibold text-white transition-all hover:bg-[#4752c4]"
                >
                  Inviter <ExternalLink className="h-3 w-3" />
                </a>
                {bot.vote && (
                  <a
                    href={bot.vote}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg bg-white/[0.06] px-3 py-1.5 text-xs font-medium text-neutral-300 ring-1 ring-white/10 transition-all hover:bg-white/[0.1]"
                  >
                    Voter
                  </a>
                )}
                <Link
                  href={`/discord/${bot.slug}`}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-neutral-300 transition-all hover:bg-white/[0.06]"
                >
                  Voir plus <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-10 text-center">
          <p className="text-sm text-neutral-500">
            Besoin d&apos;un bot sur mesure ?{" "}
            <a href="https://discord.gg/p768u2Pgp3" target="_blank" rel="noopener noreferrer" className="text-[#00e1ff] hover:underline">
              Contactez-nous sur Discord
            </a>
          </p>
        </div>
      </section>

      {/* AUTRES PROJETS */}
      <section id="autres" className="relative border-y border-white/[0.04] bg-white/[0.01]">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-violet-500/10 px-4 py-1.5 text-sm text-violet-300 mb-6">
              <Sparkles className="h-4 w-4" />
              Autres projets
            </div>
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Multivers Synkrone
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-neutral-400">
              Découvrez les autres projets développés par l&apos;équipe Synkrone et sa communauté.
            </p>
          </div>
          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <div className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:-translate-y-1 hover:bg-white/[0.04]">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-violet-500/10 text-violet-400 ring-1 ring-white/10">
                <BrainCircuit className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">Maths-App</h3>
              <p className="mt-1 text-sm text-violet-400">Le chess.com des mathématiques</p>
              <p className="mt-2 text-sm text-neutral-400">
                Tests d&apos;évaluation, exercices adaptatifs, multijoueur temps réel et classement Elo.
              </p>
              <a
                href="https://maths-app.com"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-violet-400 transition-colors hover:text-violet-300"
              >
                Lancer <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
            <Link href="/minecraft" className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:-translate-y-1 hover:bg-white/[0.04]">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 ring-1 ring-white/10">
                <Blocks className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">Projets Minecraft</h3>
              <p className="mt-1 text-sm text-emerald-400">Modpacks & serveurs</p>
              <p className="mt-2 text-sm text-neutral-400">
                The French Baguette, Xenus, Vanipack et le serveur Cantale.
              </p>
              <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-emerald-400 transition-colors hover:text-emerald-300">
                Découvrir <ArrowRight className="h-3.5 w-3.5" />
              </span>
            </Link>
            <Link href="/website-creator" className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 transition-all hover:-translate-y-1 hover:bg-white/[0.04]">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 ring-1 ring-white/10">
                <Globe className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-semibold text-white">Créateur Web</h3>
              <p className="mt-1 text-sm text-cyan-400">Site pour votre serveur</p>
              <p className="mt-2 text-sm text-neutral-400">
                Composez une page vitrine pour votre communauté sans écrire de code.
              </p>
              <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-cyan-400 transition-colors hover:text-cyan-300">
                En savoir plus <ArrowRight className="h-3.5 w-3.5" />
              </span>
            </Link>
          </div>
        </div>
      </section>

      {/* EQUIPE */}
      <section id="equipes" className="mx-auto max-w-7xl px-6 py-24">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-4 py-1.5 text-sm text-amber-300 mb-6">
            <Users className="h-4 w-4" />
            L&apos;équipe
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Les architectes de Synkrone
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-neutral-400">
            Une petite équipe passionnée qui construit des outils puissants pour les communautés Discord.
          </p>
        </div>
        <div className="mt-14 grid gap-8 sm:grid-cols-2 max-w-3xl mx-auto">
          {[
            {
              name: "VEX",
              role: "Lead dev. Architecture logicielle et bots Discord.",
              color: "indigo",
              icon: Cpu,
              github: "https://github.com/vex",
            },
            {
              name: "Ønyx",
              role: "Infrastructure & cloud. Stabilité des systèmes.",
              color: "emerald",
              icon: Server,
              github: "https://github.com/Annonnyx",
            },
          ].map((member) => (
            <div
              key={member.name}
              className="group relative rounded-2xl border border-white/[0.06] bg-white/[0.02] p-8 transition-all hover:-translate-y-1 hover:bg-white/[0.04]"
            >
              <div className={`mb-5 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-${member.color}-500/10 text-${member.color}-400 ring-1 ring-white/10`}>
                <member.icon className="h-7 w-7" />
              </div>
              <h3 className="text-xl font-bold text-white">{member.name}</h3>
              <p className={`mt-1 text-sm font-medium text-${member.color}-400`}>{member.role}</p>
              {member.github && (
                <a
                  href={member.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-flex items-center gap-1.5 text-sm text-neutral-400 hover:text-neutral-300"
                >
                  GitHub <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          ))}
        </div>

        <div className="mt-14 rounded-2xl border border-white/[0.06] bg-gradient-to-br from-[#00e1ff]/10 to-[#5865F2]/10 p-8 text-center">
          <h3 className="text-xl font-bold text-white">On recrute !</h3>
          <p className="mt-2 text-neutral-400">Tu veux contribuer à Synkrone ? Tous les profils sont les bienvenus.</p>
          <div className="mt-5 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <a
              href="https://discord.gg/nuFNvVybGE"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#00e1ff] to-[#5865F2] px-6 py-3 text-sm font-semibold text-[#0a0a0a] shadow-lg shadow-cyan-500/20 transition-all hover:brightness-110"
            >
              Rejoindre le Discord <ArrowRight className="h-4 w-4" />
            </a>
            <a
              href="mailto:contact@synkrone.fr"
              className="inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-6 py-3 text-sm font-semibold text-neutral-200 transition-all hover:bg-white/[0.06]"
            >
              Nous contacter
            </a>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative mx-6 mb-6 overflow-hidden rounded-3xl">
        <div className="absolute inset-0 bg-gradient-to-br from-[#00e1ff]/20 via-[#5865F2]/15 to-[#a855f7]/10" />
        <div className="absolute inset-0 grid-bg opacity-30" />
        <div className="relative mx-auto max-w-4xl px-6 py-20 text-center">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Prêt à créer votre bot ?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-neutral-300">
            Pas de carte requise. Testez tous les modules gratuitement.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href={isLoggedIn ? "/dashboard" : "/login"}
              className="inline-flex items-center gap-2 rounded-xl bg-white px-8 py-3.5 text-base font-semibold text-[#0a0a0a] shadow-lg transition-all hover:bg-neutral-200 hover:scale-[1.02]"
            >
              {isLoggedIn ? "Lancer le dashboard" : "Créer mon compte gratuit"}
              <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="https://discord.gg/nuFNvVybGE"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-8 py-3.5 text-base font-semibold text-neutral-200 transition-all hover:bg-white/[0.06]"
            >
              Rejoindre Discord
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
