"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

type CommandDef = {
  id: string;
  name: string;
  description: string;
  category: string;
  priceKr: number;
  premium: boolean;
};

type BotData = {
  id: string;
  botName: string;
  cogs: string[];
  kronesConsumed: number;
};

export default function BotModulesPage() {
  const params = useParams();
  const router = useRouter();
  const botId = params.botId as string;

  const [bot, setBot] = useState<BotData | null>(null);
  const [commands, setCommands] = useState<CommandDef[]>([]);
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch(`/api/bots/${botId}`).then((r) => r.json()),
      fetch("/api/commands").then((r) => r.json()),
    ])
      .then(([botData, cmds]) => {
        setBot(botData);
        setCommands(Array.isArray(cmds) ? cmds : []);
        setLoading(false);
      })
      .catch(() => {
        setError("Impossible de charger les données");
        setLoading(false);
      });
  }, [botId]);

  const ownedCogs = new Set(bot?.cogs ?? []);
  const available = commands.filter((c) => !ownedCogs.has(c.id) && !c.premium);
  const grouped = available.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = [];
    acc[cmd.category].push(cmd);
    return acc;
  }, {} as Record<string, CommandDef[]>);

  async function buyModule(commandId: string) {
    setBuying(commandId);
    setError(null);
    try {
      const res = await fetch(`/api/bots/${botId}/modules`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ commandId }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur lors de l'achat");
      } else {
        setBot((prev) =>
          prev
            ? { ...prev, cogs: [...prev.cogs, commandId], kronesConsumed: prev.kronesConsumed + (data.priceKr ?? 0) }
            : prev
        );
        setSuccessMsg("Module ajouté ! Redémarrage nécessaire.");
        setTimeout(() => setSuccessMsg(null), 3000);
      }
    } catch {
      setError("Erreur réseau");
    } finally {
      setBuying(null);
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-neutral-400">Chargement...</p>
      </div>
    );
  }

  if (!bot) {
    return (
      <div className="p-8">
        <p className="text-red-400">{error ?? "Bot introuvable"}</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl">
      <div className="flex items-center gap-4 mb-6">
        <Link
          href={`/dashboard/bots/${botId}`}
          className="text-sm text-neutral-400 hover:text-white"
        >
          ← Retour
        </Link>
        <h1 className="text-2xl font-bold text-white">Ajouter des modules — {bot.botName}</h1>
      </div>

      {successMsg && (
        <div className="mb-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-400">
          {successMsg}
        </div>
      )}
      {error && (
        <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      {Object.entries(grouped).length === 0 ? (
        <p className="text-neutral-400">Tous les modules disponibles sont déjà activés.</p>
      ) : (
        Object.entries(grouped).map(([category, cmds]) => (
          <div key={category} className="mb-8">
            <h2 className="text-lg font-semibold text-white mb-3">{category}</h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {cmds.map((cmd) => (
                <div
                  key={cmd.id}
                  className="rounded-xl border border-neutral-800 bg-neutral-900 p-4"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-medium text-white">{cmd.name}</h3>
                      <p className="mt-1 text-sm text-neutral-400">{cmd.description}</p>
                    </div>
                    <span className="rounded-full bg-indigo-500/10 px-2.5 py-1 text-xs font-medium text-indigo-400">
                      {cmd.priceKr} Kr
                    </span>
                  </div>
                  <button
                    onClick={() => buyModule(cmd.id)}
                    disabled={buying === cmd.id}
                    className="mt-4 w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
                  >
                    {buying === cmd.id ? "Achat..." : "Acheter et ajouter"}
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
