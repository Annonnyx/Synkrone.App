"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { StatusBadge } from "@/components/ui/StatusBadge";

type Bot = {
  id: string;
  botName: string;
  prefix: string;
  status: string;
  kronesConsumed: number;
};

export default function BotsPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/user/services")
      .then((r) => r.json())
      .then((data) => {
        setBots(data.bots ?? []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-neutral-400">Chargement...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Mes Bots Discord</h1>
        <Link
          href="/dashboard/bots/new"
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
        >
          + Créer un bot Discord
        </Link>
      </div>

      {bots.length === 0 ? (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-8 text-center">
          <p className="text-neutral-400">Vous n'avez pas encore de bots Discord.</p>
          <Link
            href="/dashboard/bots/new"
            className="mt-4 inline-block rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
          >
            Créer mon premier bot
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {bots.map((bot) => (
            <div key={bot.id} className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white truncate">{bot.botName}</h3>
                <StatusBadge status={bot.status as any} />
              </div>
              <div className="flex items-center gap-4 text-sm text-neutral-400">
                <span>Préfixe : <span className="text-white font-mono">{bot.prefix}</span></span>
                <span>{bot.kronesConsumed} Kr dépensés</span>
              </div>
              <Link
                href={`/dashboard/bots/${bot.id}`}
                className="mt-auto w-full rounded-lg bg-neutral-800 px-4 py-2 text-center text-sm font-medium text-white transition-colors hover:bg-neutral-700"
              >
                Gérer
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
