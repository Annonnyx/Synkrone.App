"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { StatusBadge } from "@/components/ui/StatusBadge";

type Tab = "logs" | "settings" | "stats";

type BotData = {
  id: string;
  botName: string;
  prefix: string;
  discordClientId: string | null;
  slashCommands: boolean;
  cogs: string[];
  status: string;
  kronesConsumed: number;
  stats: {
    serversCount: number;
    commandsTotal: number;
    errorsLast24h: number;
    uptimeSeconds: number;
  } | null;
};

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (d > 0) return `${d}j ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  return `${m}m ${s}s`;
}

export default function BotDetailPage() {
  const params = useParams();
  const botId = params.botId as string;

  const [bot, setBot] = useState<BotData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("logs");
  const [logs, setLogs] = useState("");
  const [logsLoading, setLogsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Settings state
  const [displayName, setDisplayName] = useState("");
  const [prefix, setPrefix] = useState("");
  const [clientId, setClientId] = useState("");
  const [slashCmds, setSlashCmds] = useState(false);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const router = useRouter();

  useEffect(() => {
    fetch(`/api/bots/${botId}`)
      .then((r) => r.json())
      .then((data: BotData) => {
        setBot(data);
        setDisplayName(data.botName);
        setPrefix(data.prefix || "");
        setClientId(data.discordClientId || "");
        setSlashCmds(data.slashCommands);
        setLoading(false);
      })
      .catch(() => {
        setError("Impossible de charger les données du bot");
        setLoading(false);
      });
  }, [botId]);

  async function handleAction(action: "start" | "stop" | "restart") {
    setActionLoading(action);
    setError(null);
    try {
      const res = await fetch(`/api/bots/${botId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur lors de l'action");
      } else if (bot) {
        setBot({ ...bot, status: data.status });
        setSuccessMsg(`Action "${action}" effectuée`);
        setTimeout(() => setSuccessMsg(null), 3000);
      }
    } catch {
      setError("Erreur réseau");
    } finally {
      setActionLoading(null);
    }
  }

  async function fetchLogs() {
    setLogsLoading(true);
    try {
      const res = await fetch(`/api/bots/${botId}/logs`);
      const data = await res.json();
      setLogs(data.logs ?? "Aucun log disponible.");
    } catch {
      setLogs("Erreur de chargement des logs.");
    } finally {
      setLogsLoading(false);
    }
  }

  async function handleDelete() {
    setDeleteLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/bots/${botId}`, { method: "DELETE" });
      if (res.ok) {
        router.push("/dashboard/bots");
      } else {
        const data = await res.json();
        setError(data.error ?? "Erreur lors de la suppression");
        setDeleteLoading(false);
      }
    } catch {
      setError("Erreur réseau");
      setDeleteLoading(false);
    }
  }

  async function saveSettings() {
    setSettingsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/bots/${botId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ botName: displayName, prefix, discordClientId: clientId || null }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur de sauvegarde");
      } else {
        setBot((prev) => (prev ? { ...prev, botName: data.botName, prefix: data.prefix } : prev));
        setSuccessMsg("Paramètres sauvegardés");
        setTimeout(() => setSuccessMsg(null), 3000);
      }
    } catch {
      setError("Erreur réseau");
    } finally {
      setSettingsLoading(false);
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
      {/* En-tête */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white">{bot.botName}</h1>
          <StatusBadge status={bot.status as any} />
        </div>
        <div className="flex gap-2">
          {(["start", "stop", "restart"] as const).map((action) => (
            <button
              key={action}
              onClick={() => handleAction(action)}
              disabled={!!actionLoading}
              className="rounded-lg bg-neutral-800 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-neutral-700 disabled:opacity-50"
            >
              {actionLoading === action ? (
                <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                action === "start" ? "Démarrer" : action === "stop" ? "Arrêter" : "Redémarrer"
              )}
            </button>
          ))}
        </div>
      </div>

      {successMsg && (
        <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-400">
          {successMsg}
        </div>
      )}
      {error && (
        <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Onglets */}
      <div className="mt-8 flex gap-1 border-b border-neutral-800">
        {(["logs", "settings", "stats"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === t
                ? "border-b-2 border-indigo-500 text-white"
                : "text-neutral-400 hover:text-white"
            }`}
          >
            {t === "logs" ? "Logs" : t === "settings" ? "Paramètres" : "Statistiques"}
          </button>
        ))}
      </div>

      {/* Contenu onglet */}
      <div className="mt-6">
        {tab === "logs" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-neutral-500">Les logs sont en lecture seule.</p>
              <button
                onClick={fetchLogs}
                disabled={logsLoading}
                className="rounded-lg bg-neutral-800 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-neutral-700 disabled:opacity-50"
              >
                {logsLoading ? "Chargement..." : "Actualiser les logs"}
              </button>
            </div>
            <pre className="h-96 overflow-auto rounded-xl border border-neutral-800 bg-[#0a0a0a] p-4 font-mono text-xs text-emerald-400 whitespace-pre-wrap">
              {logs || "Cliquez sur \"Actualiser les logs\" pour charger."}
            </pre>
          </div>
        )}

        {tab === "settings" && (
          <div className="space-y-6 max-w-xl">
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-1.5">Nom affiché</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-1.5">Préfixe</label>
              <input
                type="text"
                value={prefix}
                onChange={(e) => setPrefix(e.target.value)}
                className="w-16 rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white text-center focus:border-indigo-500 focus:outline-none"
                maxLength={1}
              />
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSlashCmds((s) => !s)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${slashCmds ? "bg-indigo-600" : "bg-neutral-700"}`}
              >
                <span className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${slashCmds ? "translate-x-6" : "translate-x-1"}`} />
              </button>
              <span className="text-sm text-neutral-300">Slash commands {slashCmds ? "(activé +100 Kr)" : ""}</span>
            </div>
            <button
              onClick={saveSettings}
              disabled={settingsLoading}
              className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
            >
              {settingsLoading ? "Sauvegarde..." : "Sauvegarder les paramètres"}
            </button>

            <div className="border-t border-red-500/20 pt-6">
              <h3 className="text-lg font-semibold text-red-400 mb-4">Zone dangereuse</h3>
              {!deleteConfirm ? (
                <button
                  onClick={() => setDeleteConfirm(true)}
                  className="rounded-xl border border-red-500/30 bg-red-500/10 px-6 py-2.5 text-sm font-semibold text-red-400 transition-colors hover:bg-red-500/20"
                >
                  Supprimer ce bot
                </button>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-red-400">Cette action est irréversible. Confirmer ?</p>
                  <div className="flex gap-3">
                    <button
                      onClick={handleDelete}
                      disabled={deleteLoading}
                      className="rounded-xl bg-red-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-red-500 disabled:opacity-50"
                    >
                      {deleteLoading ? "Suppression..." : "Oui, supprimer"}
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(false)}
                      disabled={deleteLoading}
                      className="rounded-xl border border-neutral-800 bg-neutral-900 px-6 py-2.5 text-sm font-medium text-neutral-300 transition-colors hover:bg-neutral-800"
                    >
                      Annuler
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="border-t border-neutral-800 pt-6">
              <h3 className="text-lg font-semibold text-white mb-4">Modules actifs</h3>
              {bot.cogs.length === 0 ? (
                <p className="text-sm text-neutral-500">Aucun module activé.</p>
              ) : (
                <div className="space-y-2">
                  {bot.cogs.map((cog) => (
                    <div key={cog} className="flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2.5">
                      <span className="text-sm text-white">{cog}</span>
                      <button
                        onClick={() => {
                          /* TODO: retirer module + créditer Kr */
                        }}
                        className="text-xs text-red-400 hover:text-red-300"
                      >
                        Retirer
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <Link
                href={`/dashboard/bots/${botId}/modules`}
                className="mt-4 inline-block rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2 text-sm text-neutral-300 hover:border-indigo-500/30 hover:text-white transition-colors"
              >
                Ajouter des modules
              </Link>
            </div>
          </div>
        )}

        {tab === "stats" && (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
                <p className="text-sm text-neutral-400">Serveurs Discord</p>
                <p className="mt-1 text-2xl font-bold text-white">{bot.stats?.serversCount ?? 0}</p>
              </div>
              <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
                <p className="text-sm text-neutral-400">Commandes totales</p>
                <p className="mt-1 text-2xl font-bold text-white">{bot.stats?.commandsTotal ?? 0}</p>
              </div>
              <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
                <p className="text-sm text-neutral-400">Erreurs 24h</p>
                <p className="mt-1 text-2xl font-bold text-white">{bot.stats?.errorsLast24h ?? 0}</p>
              </div>
              <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
                <p className="text-sm text-neutral-400">Uptime</p>
                <p className="mt-1 text-2xl font-bold text-white">{formatUptime(bot.stats?.uptimeSeconds ?? 0)}</p>
              </div>
            </div>
            <p className="text-sm text-neutral-500">Les statistiques se mettent à jour toutes les heures.</p>
          </div>
        )}
      </div>
    </div>
  );
}
