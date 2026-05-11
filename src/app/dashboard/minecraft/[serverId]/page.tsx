"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { KrBadge } from "@/components/ui/KrBadge";

type Tab = "console" | "sftp" | "storage" | "settings" | "backups";

type Backup = {
  id: string;
  filePath: string;
  sizeMb: number;
  type: string;
  createdAt: string;
};

type ServerData = {
  id: string;
  serverName: string;
  version: string;
  ramMb: number;
  storageQuotaMb: number;
  storageUsedMb: number;
  gameMode: string;
  difficulty: string;
  pvp: boolean;
  maxPlayers: number;
  status: string;
  dirPath: string;
  sftpUser: string;
  sftpPasswordEnc: string;
  pm2Name: string;
  kronesPerMonth: number;
  backups: Backup[];
};


export default function MinecraftServerPage() {
  const params = useParams();
  const serverId = params.serverId as string;
  const { data: session } = useSession();
  const userRoles = session?.user?.roles ?? [];
  const isSupportPlus = userRoles.some((r) => ["SUPPORT", "DEV_TEST", "DEV_DEV", "DEV_ELITE", "MANAGER", "SUPERVISOR", "LEADER"].includes(r));

  const [server, setServer] = useState<ServerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("console");
  const [logs, setLogs] = useState("");
  const [logsLoading, setLogsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [sftpPassword, setSftpPassword] = useState("");
  const [sftpLoading, setSftpLoading] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);

  // Settings
  const [editName, setEditName] = useState("");
  const [editRam, setEditRam] = useState(2);
  const [editMaxPlayers, setEditMaxPlayers] = useState(20);
  const [settingsLoading, setSettingsLoading] = useState(false);

  useEffect(() => {
    fetch(`/api/minecraft/${serverId}`)
      .then((r) => r.json())
      .then((data: ServerData) => {
        setServer(data);
        setEditName(data.serverName);
        setEditRam(Math.round(data.ramMb / 1024));
        setEditMaxPlayers(data.maxPlayers);
        setLoading(false);
      })
      .catch(() => {
        setError("Impossible de charger les données du serveur");
        setLoading(false);
      });
  }, [serverId]);

  async function handleAction(action: "start" | "stop" | "restart" | "save") {
    setActionLoading(action);
    setError(null);
    try {
      const res = await fetch(`/api/minecraft/${serverId}/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur lors de l'action");
      } else if (server) {
        setServer({ ...server, status: data.status ?? server.status });
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
      const res = await fetch(`/api/minecraft/${serverId}/logs`);
      const data = await res.json();
      setLogs(data.logs ?? "Aucun log disponible.");
    } catch {
      setLogs("Erreur de chargement des logs.");
    } finally {
      setLogsLoading(false);
    }
  }

  async function fetchSftp() {
    setSftpLoading(true);
    try {
      const res = await fetch(`/api/minecraft/${serverId}/sftp`);
      const data = await res.json();
      if (res.ok) setSftpPassword(data.password ?? "");
    } catch {
      setError("Erreur de chargement des identifiants SFTP");
    } finally {
      setSftpLoading(false);
    }
  }

  async function handleBackup() {
    setBackupLoading(true);
    try {
      const res = await fetch(`/api/minecraft/${serverId}/backup`, { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        setSuccessMsg("Sauvegarde créée");
        setTimeout(() => setSuccessMsg(null), 3000);
        // Recharger les données
        const refresh = await fetch(`/api/minecraft/${serverId}`);
        const refreshed = await refresh.json();
        setServer(refreshed);
      } else {
        setError(data.error ?? "Erreur lors de la sauvegarde");
      }
    } catch {
      setError("Erreur réseau");
    } finally {
      setBackupLoading(false);
    }
  }

  async function saveSettings() {
    setSettingsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/minecraft/${serverId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ serverName: editName, ramMb: editRam * 1024, maxPlayers: editMaxPlayers }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur de sauvegarde");
      } else {
        setServer((prev) => (prev ? { ...prev, serverName: data.serverName, ramMb: data.ramMb, maxPlayers: data.maxPlayers } : prev));
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

  if (!server) {
    return (
      <div className="p-8">
        <p className="text-red-400">{error ?? "Serveur introuvable"}</p>
      </div>
    );
  }

  const storagePct = Math.min((server.storageUsedMb / server.storageQuotaMb) * 100, 100);
  const ramDiff = editRam - Math.round(server.ramMb / 1024);
  const krDiff = ramDiff * 50;

  return (
    <div className="p-8 max-w-5xl">
      {/* En-tête */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white">{server.serverName}</h1>
          <StatusBadge status={server.status as any} />
        </div>
        <div className="flex gap-2 flex-wrap">
          {(["start", "stop", "restart", "save"] as const).map((action) => (
            <button
              key={action}
              onClick={() => handleAction(action)}
              disabled={!!actionLoading}
              className="rounded-lg bg-neutral-800 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-neutral-700 disabled:opacity-50"
            >
              {actionLoading === action ? (
                <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                action === "start" ? "Démarrer" : action === "stop" ? "Arrêter" : action === "restart" ? "Redémarrer" : "Sauvegarder"
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
      <div className="mt-8 flex gap-1 border-b border-neutral-800 flex-wrap">
        {(["console", "sftp", "storage", "settings", "backups"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === t ? "border-b-2 border-indigo-500 text-white" : "text-neutral-400 hover:text-white"
            }`}
          >
            {t === "console" ? "Console" : t === "sftp" ? "Accès SFTP" : t === "storage" ? "Stockage" : t === "settings" ? "Paramètres" : "Backups"}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {/* CONSOLE */}
        {tab === "console" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-neutral-500">
                Lecture seule. {isSupportPlus ? "Vous pouvez saisir des commandes." : "Les membres SUPPORT et supérieurs peuvent saisir des commandes."}
              </p>
              <button
                onClick={fetchLogs}
                disabled={logsLoading}
                className="rounded-lg bg-neutral-800 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-neutral-700 disabled:opacity-50"
              >
                {logsLoading ? "Chargement..." : "Actualiser"}
              </button>
            </div>
            <pre className="h-96 overflow-auto rounded-xl border border-neutral-800 bg-[#0a0a0a] p-4 font-mono text-xs text-emerald-400 whitespace-pre-wrap">
              {logs || "Cliquez sur \"Actualiser\" pour charger les logs."}
            </pre>
          </div>
        )}

        {/* SFTP */}
        {tab === "sftp" && (
          <div className="max-w-md space-y-5">
            <p className="text-sm text-neutral-500">Connectez-vous avec FileZilla ou WinSCP pour uploader des plugins et des maps.</p>
            <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-neutral-400">Hôte</span>
                <span className="text-white font-medium">synkrone.app</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Port</span>
                <span className="text-white font-medium">22</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Utilisateur</span>
                <span className="text-white font-medium">{server.sftpUser}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-neutral-400">Mot de passe</span>
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium font-mono">
                    {showPassword && sftpPassword ? sftpPassword : "••••••••••"}
                  </span>
                  <button
                    onClick={() => {
                      if (!sftpPassword) fetchSftp();
                      setShowPassword((s) => !s);
                    }}
                    disabled={sftpLoading}
                    className="text-xs text-neutral-400 hover:text-white"
                  >
                    {sftpLoading ? "Chargement..." : showPassword ? "Masquer" : "Révéler"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* STOCKAGE */}
        {tab === "storage" && (
          <div className="max-w-xl space-y-6">
            <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-neutral-400">Utilisé</span>
                <span className="text-white font-medium">{server.storageUsedMb.toLocaleString("fr-FR")} / {server.storageQuotaMb.toLocaleString("fr-FR")} Mo</span>
              </div>
              <div className="h-3 w-full rounded-full bg-neutral-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-indigo-500 transition-all"
                  style={{ width: `${storagePct}%` }}
                />
              </div>
            </div>
            <button className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500">
              Augmenter le stockage (+1 Go : 50 Kr/mois)
            </button>
          </div>
        )}

        {/* PARAMÈTRES */}
        {tab === "settings" && (
          <div className="max-w-xl space-y-5">
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-1.5">Nom du serveur</label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-1.5">RAM : {editRam} Go {krDiff !== 0 && <KrBadge amount={krDiff * 50} showSign />}</label>
              <input
                type="range"
                min={1}
                max={16}
                step={1}
                value={editRam}
                onChange={(e) => setEditRam(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-300 mb-1.5">Joueurs max : {editMaxPlayers}</label>
              <input
                type="range"
                min={1}
                max={100}
                step={1}
                value={editMaxPlayers}
                onChange={(e) => setEditMaxPlayers(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <button
              onClick={saveSettings}
              disabled={settingsLoading}
              className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
            >
              {settingsLoading ? "Sauvegarde..." : "Sauvegarder"}
            </button>
          </div>
        )}

        {/* BACKUPS */}
        {tab === "backups" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Sauvegardes</h3>
              <button
                onClick={handleBackup}
                disabled={backupLoading}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
              >
                {backupLoading ? "Création..." : "Créer une sauvegarde manuelle"}
              </button>
            </div>
            {server.backups.length === 0 ? (
              <p className="text-sm text-neutral-500">Aucune sauvegarde.</p>
            ) : (
              <div className="grid gap-3">
                {server.backups.map((b) => (
                  <div key={b.id} className="flex items-center justify-between rounded-xl border border-neutral-800 bg-neutral-900 px-5 py-3">
                    <div className="flex items-center gap-3">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${b.type === "AUTO" ? "bg-neutral-800 text-neutral-400" : "bg-indigo-500/10 text-indigo-400"}`}>
                        {b.type}
                      </span>
                      <span className="text-sm text-white">{new Date(b.createdAt).toLocaleString("fr-FR")}</span>
                    </div>
                    <span className="text-sm text-neutral-400">{b.sizeMb.toFixed(1)} Mo</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
