"use client";

import Link from "next/link";
import { ArrowLeft, Bot, ExternalLink, MessageCircle, ArrowRight } from "lucide-react";
import { discordBots } from "@/lib/discord-bots";

export default function DiscordPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-50">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white">
          <ArrowLeft className="h-4 w-4" />
          Retour à l&apos;accueil
        </Link>

        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-4 py-1.5 text-sm text-indigo-300 mb-6">
            <Bot className="h-4 w-4" />
            Bots Discord
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Nos bots
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-neutral-400">
            Une suite de bots Discord pensée pour enrichir vos serveurs. Modération, casino, collection et utilitaires.
          </p>
        </div>

        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {discordBots.map((bot) => (
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

              {bot.commands && (
                <div className="mt-4 space-y-2">
                  {bot.commands.map((cat) => (
                    <div key={cat.category}>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-neutral-500">{cat.category}</span>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {cat.cmds.map((cmd) => (
                          <span
                            key={cmd}
                            className="rounded bg-neutral-800 px-1.5 py-0.5 text-[10px] text-neutral-300"
                          >
                            {cmd}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

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
                  En savoir plus <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* Custom bot CTA */}
        <div className="mt-10 rounded-2xl border border-white/[0.06] bg-gradient-to-br from-[#00e1ff]/10 to-[#5865F2]/10 p-8 text-center">
          <div className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-xl bg-[#00e1ff]/10 text-[#00e1ff] ring-1 ring-white/10 mb-4">
            <Bot className="h-6 w-6" />
          </div>
          <h3 className="text-xl font-bold text-white">Bot personnalisé</h3>
          <p className="mx-auto mt-2 max-w-lg text-sm text-neutral-400">
            Besoin d&apos;un bot sur mesure pour votre serveur ? Synkrone développe des bots Discord customisés selon vos besoins.
          </p>
          <a
            href="https://discord.gg/p768u2Pgp3"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#00e1ff] to-[#5865F2] px-6 py-3 text-sm font-semibold text-[#0a0a0a] shadow-lg shadow-cyan-500/20 transition-all hover:brightness-110"
          >
            En savoir plus <ArrowRight className="h-4 w-4" />
          </a>
        </div>

        {/* Support CTA */}
        <div className="mt-8 text-center">
          <p className="text-neutral-400">Une question ? Un problème ? Rejoignez notre serveur Discord.</p>
          <a
            href="https://discord.gg/p768u2Pgp3"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-6 py-3 text-sm font-semibold text-neutral-200 transition-all hover:bg-white/[0.06]"
          >
            <MessageCircle className="h-4 w-4" />
            Synkrone Support
          </a>
        </div>
      </div>
    </div>
  );
}
