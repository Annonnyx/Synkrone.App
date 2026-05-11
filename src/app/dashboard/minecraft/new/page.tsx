"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { KrBadge } from "@/components/ui/KrBadge";

/* ─── DONNÉES ─── */
const versionOptions = [
  { label: "1.21.4 Paper", value: "1.21.4-paper" },
  { label: "1.20.4 Paper", value: "1.20.4-paper" },
  { label: "1.19.4 Paper", value: "1.19.4-paper" },
  { label: "1.21.4 Vanilla", value: "1.21.4-vanilla" },
  { label: "1.20.4 Vanilla", value: "1.20.4-vanilla" },
  { label: "1.20.4 Forge", value: "1.20.4-forge" },
  { label: "1.19.4 Forge", value: "1.19.4-forge" },
  { label: "1.21.4 Fabric", value: "1.21.4-fabric" },
  { label: "1.20.4 Fabric", value: "1.20.4-fabric" },
];

const gameModes = ["SURVIVAL", "CREATIVE", "ADVENTURE", "SPECTATOR"];
const difficulties = ["PEACEFUL", "EASY", "NORMAL", "HARD"];

/* ─── PAGE ─── */
export default function NewMinecraftPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const krBalance = session?.user?.kronesBalance ?? 0;

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [serverName, setServerName] = useState("");
  const [version, setVersion] = useState("1.21.4-paper");
  const [ramGb, setRamGb] = useState(2);
  const [gameMode, setGameMode] = useState("SURVIVAL");
  const [difficulty, setDifficulty] = useState("NORMAL");
  const [pvp, setPvp] = useState(true);
  const [maxPlayers, setMaxPlayers] = useState(20);
  const [eulaAccepted, setEulaAccepted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const ramMb = ramGb * 1024;
  const costPerMonth = ramGb * 50;
  const afterBalance = krBalance - costPerMonth;
  const hasEnough = costPerMonth <= krBalance;

  function gameModeLabel(v: string) {
    return { SURVIVAL: "Survie", CREATIVE: "Créatif", ADVENTURE: "Aventure", SPECTATOR: "Spectateur" }[v] ?? v;
  }

  function difficultyLabel(v: string) {
    return { PEACEFUL: "Paisible", EASY: "Facile", NORMAL: "Normale", HARD: "Difficile" }[v] ?? v;
  }

  async function handleCreate() {
    if (!hasEnough || !eulaAccepted) return;
    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/minecraft/provision", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          serverName: serverName.trim(),
          version,
          ramMb,
          gameMode,
          difficulty,
          pvp,
          maxPlayers,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setErrorMsg(data.error ?? "Une erreur est survenue");
        setLoading(false);
        return;
      }

      router.push(`/dashboard/minecraft/${data.serverId}`);
    } catch {
      setErrorMsg("Erreur réseau. Réessayez.");
      setLoading(false);
    }
  }

  /* ── ÉTAPE 1 ── */
  if (step === 1) {
    return (
      <div className="p-8 max-w-2xl">
        <h1 className="text-2xl font-bold text-white mb-2">Créer un serveur Minecraft</h1>
        <p className="text-neutral-400 text-sm mb-8">Étape 1 sur 3 — Configuration de base</p>

        <div className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Nom du serveur *</label>
            <input
              type="text"
              value={serverName}
              onChange={(e) => setServerName(e.target.value)}
              placeholder="MonServeurMC"
              className="w-full rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white placeholder-neutral-600 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Version Minecraft *</label>
            <select
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              className="w-full rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none appearance-none"
            >
              <optgroup label="Paper">
                <option value="1.21.4-paper">1.21.4 Paper</option>
                <option value="1.20.4-paper">1.20.4 Paper</option>
                <option value="1.19.4-paper">1.19.4 Paper</option>
              </optgroup>
              <optgroup label="Vanilla">
                <option value="1.21.4-vanilla">1.21.4 Vanilla</option>
                <option value="1.20.4-vanilla">1.20.4 Vanilla</option>
              </optgroup>
              <optgroup label="Forge">
                <option value="1.20.4-forge">1.20.4 Forge</option>
                <option value="1.19.4-forge">1.19.4 Forge</option>
              </optgroup>
              <optgroup label="Fabric">
                <option value="1.21.4-fabric">1.21.4 Fabric</option>
                <option value="1.20.4-fabric">1.20.4 Fabric</option>
              </optgroup>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">RAM : {ramGb} Go</label>
            <input
              type="range"
              min={1}
              max={16}
              step={1}
              value={ramGb}
              onChange={(e) => setRamGb(Number(e.target.value))}
              className="w-full accent-indigo-500"
            />
            <div className="flex justify-between text-xs text-neutral-500 mt-1">
              <span>1 Go</span>
              <span>16 Go</span>
            </div>
          </div>

          <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/10 px-5 py-3">
            <p className="text-sm text-indigo-300 font-medium">
              Coût mensuel : <KrBadge amount={costPerMonth} />/mois
            </p>
          </div>
        </div>

        <div className="mt-8 flex justify-end">
          <button
            onClick={() => serverName.trim() && setStep(2)}
            disabled={!serverName.trim()}
            className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Suivant
          </button>
        </div>
      </div>
    );
  }

  /* ── ÉTAPE 2 ── */
  if (step === 2) {
    return (
      <div className="p-8 max-w-2xl">
        <h1 className="text-2xl font-bold text-white mb-2">Créer un serveur Minecraft</h1>
        <p className="text-neutral-400 text-sm mb-8">Étape 2 sur 3 — Options avancées</p>

        <div className="space-y-6">
          {/* Mode de jeu */}
          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">Mode de jeu</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {gameModes.map((m) => (
                <button
                  key={m}
                  onClick={() => setGameMode(m)}
                  className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                    gameMode === m
                      ? "border-indigo-500 bg-indigo-500/10 text-white"
                      : "border-neutral-800 bg-neutral-900 text-neutral-400 hover:border-neutral-700"
                  }`}
                >
                  {gameModeLabel(m)}
                </button>
              ))}
            </div>
          </div>

          {/* Difficulté */}
          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">Difficulté</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {difficulties.map((d) => (
                <button
                  key={d}
                  onClick={() => setDifficulty(d)}
                  className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                    difficulty === d
                      ? "border-indigo-500 bg-indigo-500/10 text-white"
                      : "border-neutral-800 bg-neutral-900 text-neutral-400 hover:border-neutral-700"
                  }`}
                >
                  {difficultyLabel(d)}
                </button>
              ))}
            </div>
          </div>

          {/* PvP */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setPvp((v) => !v)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${pvp ? "bg-indigo-600" : "bg-neutral-700"}`}
            >
              <span className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${pvp ? "translate-x-6" : "translate-x-1"}`} />
            </button>
            <span className="text-sm text-neutral-300">PvP {pvp ? "activé" : "désactivé"}</span>
          </div>

          {/* Joueurs max */}
          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Joueurs max : {maxPlayers}</label>
            <input
              type="range"
              min={1}
              max={100}
              step={1}
              value={maxPlayers}
              onChange={(e) => setMaxPlayers(Number(e.target.value))}
              className="w-full accent-indigo-500"
            />
            <div className="flex justify-between text-xs text-neutral-500 mt-1">
              <span>1</span>
              <span>100</span>
            </div>
          </div>

          {/* EULA */}
          <label className="flex items-start gap-3 rounded-xl border border-neutral-800 bg-neutral-900 p-4 cursor-pointer">
            <input
              type="checkbox"
              checked={eulaAccepted}
              onChange={(e) => setEulaAccepted(e.target.checked)}
              className="mt-0.5 h-4 w-4 accent-indigo-500"
            />
            <span className="text-sm text-neutral-300">
              J'accepte les conditions d'utilisation de Mojang (EULA)
            </span>
          </label>
        </div>

        <div className="mt-8 flex justify-between">
          <button
            onClick={() => setStep(1)}
            className="rounded-xl border border-neutral-800 bg-neutral-900 px-5 py-2.5 text-sm font-medium text-neutral-300 hover:bg-neutral-800 transition-colors"
          >
            Retour
          </button>
          <button
            onClick={() => eulaAccepted && setStep(3)}
            disabled={!eulaAccepted}
            className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Suivant
          </button>
        </div>
      </div>
    );
  }

  /* ── ÉTAPE 3 ── */
  return (
    <div className="p-8 max-w-3xl pb-28">
      <h1 className="text-2xl font-bold text-white mb-2">Créer un serveur Minecraft</h1>
      <p className="text-neutral-400 text-sm mb-8">Étape 3 sur 3 — Récapitulatif</p>

      {/* Récap */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-neutral-400">Nom</span>
          <span className="text-white font-medium">{serverName}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">Version</span>
          <span className="text-white font-medium">{versionOptions.find(v => v.value === version)?.label ?? version}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">RAM</span>
          <span className="text-white font-medium">{ramGb} Go ({ramMb} Mo)</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">Mode de jeu</span>
          <span className="text-white font-medium">{gameModeLabel(gameMode)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">Difficulté</span>
          <span className="text-white font-medium">{difficultyLabel(difficulty)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">PvP</span>
          <span className="text-white font-medium">{pvp ? "Activé" : "Désactivé"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-neutral-400">Joueurs max</span>
          <span className="text-white font-medium">{maxPlayers}</span>
        </div>
        <div className="border-t border-neutral-800 pt-3 flex justify-between">
          <span className="text-neutral-400">Coût mensuel</span>
          <span className="font-bold text-white"><KrBadge amount={costPerMonth} />/mois</span>
        </div>
      </div>

      {/* Solde */}
      <div className="mt-6 rounded-xl border border-neutral-800 bg-neutral-900 p-5">
        <div className="flex flex-col gap-2 text-sm">
          <div className="flex justify-between">
            <span className="text-neutral-400">Solde avant</span>
            <KrBadge amount={krBalance} />
          </div>
          <div className="flex justify-between">
            <span className="text-neutral-400">Coût premier mois</span>
            <span className="font-medium text-red-400">- <KrBadge amount={costPerMonth} /></span>
          </div>
          <div className="flex justify-between border-t border-neutral-800 pt-2 mt-1">
            <span className="text-neutral-400">Solde après</span>
            <KrBadge amount={afterBalance} />
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 px-5 py-3 text-sm text-red-400">
          {errorMsg}
        </div>
      )}

      <div className="mt-8 flex items-center justify-between">
        <button
          onClick={() => setStep(2)}
          className="rounded-xl border border-neutral-800 bg-neutral-900 px-5 py-2.5 text-sm font-medium text-neutral-300 hover:bg-neutral-800 transition-colors"
        >
          Retour
        </button>
        {!hasEnough ? (
          <div className="flex flex-col items-end gap-2">
            <p className="text-sm text-red-400">Solde insuffisant pour créer ce serveur</p>
            <button
              onClick={() => router.push("/dashboard/krones")}
              className="rounded-xl bg-yellow-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-yellow-500"
            >
              Acheter des Krônes
            </button>
          </div>
        ) : loading ? (
          <div className="flex items-center gap-3 rounded-xl bg-indigo-600/80 px-6 py-2.5 text-sm font-semibold text-white">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            Création en cours...
          </div>
        ) : (
          <button
            onClick={handleCreate}
            className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
          >
            Créer mon serveur Minecraft
          </button>
        )}
      </div>
    </div>
  );
}
