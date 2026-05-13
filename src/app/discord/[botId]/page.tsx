"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ExternalLink, Bot, Wrench, Layers, Dices } from "lucide-react";
import { discordBots, DiscordBot } from "@/lib/discord-bots";

function BotPageClient({ bot }: { bot: DiscordBot }) {
  const Icon = bot.icon;

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-50">
      <div className="mx-auto max-w-5xl px-6 py-12">
        <Link
          href="/discord"
          className="mb-8 inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" /> Retour aux bots
        </Link>

        {/* Hero */}
        <div className="flex flex-col items-start gap-6 sm:flex-row sm:items-center">
          <div
            className={`inline-flex h-20 w-20 items-center justify-center rounded-2xl bg-${bot.color}-500/10 text-${bot.color}-400 ring-1 ring-white/10`}
          >
            <Icon className="h-10 w-10" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-white sm:text-4xl">{bot.name}</h1>
              <span
                className={`rounded-md bg-${bot.color}-500/20 px-2 py-0.5 text-xs font-bold uppercase tracking-wider text-${bot.color}-300`}
              >
                {bot.tag}
              </span>
            </div>
            <p className="mt-2 max-w-xl text-neutral-400">{bot.longDesc}</p>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-8 flex flex-wrap gap-3">
          <a
            href={bot.invite}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl bg-[#5865F2] px-6 py-3 text-sm font-semibold text-white transition-all hover:bg-[#4752c4]"
          >
            Inviter sur Discord <ExternalLink className="h-4 w-4" />
          </a>
          {bot.vote && (
            <a
              href={bot.vote}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-6 py-3 text-sm font-semibold text-neutral-200 transition-all hover:bg-white/[0.06]"
            >
              Voter sur Top.gg <ExternalLink className="h-4 w-4" />
            </a>
          )}
          <a
            href={bot.support}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.03] px-6 py-3 text-sm font-semibold text-neutral-200 transition-all hover:bg-white/[0.06]"
          >
            Serveur de support <ExternalLink className="h-4 w-4" />
          </a>
        </div>

        {/* Features */}
        <div className="mt-14">
          <h2 className="text-xl font-bold text-white">Fonctionnalités</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {bot.features.map((feat) => (
              <div
                key={feat}
                className="flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4"
              >
                <span className={`mt-0.5 h-2 w-2 rounded-full bg-${bot.color}-400`} />
                <span className="text-sm text-neutral-300">{feat}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Commands */}
        <div className="mt-14">
          <h2 className="text-xl font-bold text-white">Commandes</h2>
          <div className="mt-4 grid gap-6 sm:grid-cols-2">
            {bot.commands.map((cat) => (
              <div
                key={cat.category}
                className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5"
              >
                <h3 className={`text-sm font-bold uppercase tracking-wider text-${bot.color}-400`}>
                  {cat.category}
                </h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  {cat.cmds.map((cmd) => (
                    <span
                      key={cmd}
                      className="rounded bg-neutral-800 px-2 py-1 text-xs text-neutral-300"
                    >
                      {cmd}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function BotDetailPage() {
  const params = useParams<{ botId: string }>();
  const bot = discordBots.find((b) => b.slug === params.botId);
  if (!bot) notFound();
  return <BotPageClient bot={bot} />;
}
