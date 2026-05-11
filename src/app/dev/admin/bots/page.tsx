"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { KrBadge } from "@/components/ui/KrBadge";

type Bot = {
  id: string;
  botName: string;
  ownerName: string;
  prefix: string;
  cogs: string[];
  status: string;
  kronesConsumed: number;
  groupId: string | null;
  createdAt: string;
};

export default function AdminBotsPage() {
  const [bots, setBots] = useState<Bot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/admin/bots")
      .then((r) => r.json())
      .then((data: Bot[]) => {
        setBots(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Erreur de chargement");
        setLoading(false);
      });
  }, []);

  async function handleAction(botId: string, action: "restart" | "stop") {
    setActionLoading(`${botId}-${action}`);
    setError(null);
    try {
      const res = await fetch(`/api/bots/${botId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur");
      } else {
        setBots((prev) => prev.map((b) => (b.id === botId ? { ...b, status: data.status ?? b.status } : b)));
      }
    } catch {
      setError("Erreur réseau");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDelete(botId: string, botName: string) {
    if (!confirm(`Supprimer le bot "${botName}" ? Cette action est irréversible.`)) return;
    try {
      const res = await fetch(`/api/bots/${botId}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur de suppression");
      } else {
        setBots((prev) => prev.filter((b) => b.id !== botId));
      }
    } catch {
      setError("Erreur réseau");
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-neutral-400">Chargement...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl space-y-6">
      <h1 className="text-2xl font-bold text-white">Tous les Bots</h1>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 bg-neutral-900/80 text-left">
              <th className="px-4 py-3 font-medium text-neutral-400">Nom</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Propriétaire</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Statut</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Cogs</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Kr</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Groupe</th>
              <th className="px-4 py-3 font-medium text-neutral-400 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {bots.map((bot) => (
              <tr key={bot.id} className="border-b border-neutral-800/50">
                <td className="px-4 py-3 text-white font-medium">{bot.botName}</td>
                <td className="px-4 py-3 text-neutral-300">{bot.ownerName}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={bot.status as any} />
                </td>
                <td className="px-4 py-3 text-neutral-300">{bot.cogs.length}</td>
                <td className="px-4 py-3"><KrBadge amount={bot.kronesConsumed} /></td>
                  <td className="px-4 py-3 text-neutral-400 text-xs">{bot.groupId ?? "—"}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex gap-2 justify-end">
                      <Link
                        href={`/dashboard/bots/${bot.id}`}
                        className="text-xs text-cyan-400 hover:underline"
                      >
                        Voir
                      </Link>
                      <button
                        onClick={() => handleAction(bot.id, "restart")}
                        disabled={!!actionLoading}
                        className="text-xs text-indigo-400 hover:underline disabled:opacity-50"
                      >
                        {actionLoading === `${bot.id}-restart` ? "..." : "Redémarrer"}
                      </button>
                      <button
                        onClick={() => handleAction(bot.id, "stop")}
                        disabled={!!actionLoading}
                        className="text-xs text-amber-400 hover:underline disabled:opacity-50"
                      >
                        {actionLoading === `${bot.id}-stop` ? "..." : "Arrêter"}
                      </button>
                      <button
                        onClick={() => handleDelete(bot.id, bot.botName)}
                        className="text-xs text-red-400 hover:underline"
                      >
                        Supprimer
                      </button>
                    </div>
                  </td>
                </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
