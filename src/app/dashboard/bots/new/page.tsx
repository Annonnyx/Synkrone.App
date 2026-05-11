"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { KrBadge } from "@/components/ui/KrBadge";

/* ─── ÉTAT ─── */
interface ModuleDef {
  id: string;
  name: string;
  commands: { id: string; name: string; price: number }[];
  flatPrice?: number; // prix module entier
}

interface ApiCommand {
  id: string;
  name: string;
  category: string;
  module: string;
  priceKr: number;
}

const fallbackModules: ModuleDef[] = [
  {
    id: "moderation",
    name: "MODÉRATION",
    commands: [
      { id: "moderation.ban", name: "ban", price: 15 },
      { id: "moderation.kick", name: "kick", price: 15 },
      { id: "moderation.mute", name: "mute", price: 15 },
      { id: "moderation.warn", name: "warn", price: 10 },
      { id: "moderation.slowmode", name: "slowmode", price: 5 },
      { id: "moderation.purge", name: "purge", price: 10 },
      { id: "moderation.lock", name: "lock", price: 10 },
      { id: "moderation.unlock", name: "unlock", price: 10 },
    ],
  },
  {
    id: "fun",
    name: "FUN",
    commands: [
      { id: "fun.poll", name: "poll", price: 10 },
      { id: "fun.roulette", name: "roulette", price: 10 },
      { id: "fun.8ball", name: "8ball", price: 5 },
      { id: "fun.blague", name: "blague", price: 5 },
    ],
  },
  {
    id: "utility",
    name: "UTILITAIRES",
    commands: [
      { id: "utility.ping", name: "ping", price: 5 },
      { id: "utility.serverinfo", name: "serverinfo", price: 5 },
      { id: "utility.userinfo", name: "userinfo", price: 5 },
      { id: "utility.embed", name: "embed", price: 10 },
      { id: "utility.annonce", name: "annonce", price: 10 },
    ],
  },
  {
    id: "economy",
    name: "ÉCONOMIE",
    commands: [
      { id: "economy.balance", name: "balance", price: 20 },
      { id: "economy.work", name: "work", price: 20 },
      { id: "economy.shop", name: "shop", price: 30 },
      { id: "economy.give", name: "give", price: 10 },
      { id: "economy.leaderboard", name: "leaderboard économique", price: 20 },
    ],
  },
  {
    id: "xp",
    name: "XP / NIVEAUX",
    commands: [
      { id: "xp.rank", name: "rank", price: 20 },
      { id: "xp.leaderboard", name: "leaderboard XP", price: 20 },
      { id: "xp.rewards", name: "récompenses par niveau", price: 60 },
    ],
  },
  { id: "music", name: "MUSIQUE", commands: [], flatPrice: 200 },
  { id: "ai", name: "IA / CHATBOT", commands: [], flatPrice: 300 },
  { id: "welcome", name: "BIENVENUE / AU REVOIR", commands: [], flatPrice: 30 },
  { id: "tickets", name: "TICKETS", commands: [], flatPrice: 50 },
  { id: "giveaways", name: "GIVEAWAYS", commands: [], flatPrice: 40 },
  { id: "logs", name: "LOGS", commands: [], flatPrice: 30 },
  { id: "autoroles", name: "AUTO-RÔLES", commands: [], flatPrice: 40 },
  { id: "reactions", name: "RÉACTIONS", commands: [], flatPrice: 30 },
];

/* ─── MODALE ─── */
function HelpModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;
  const steps = [
    "Rendez-vous sur discord.com/developers/applications",
    "Cliquez \"New Application\", donnez un nom, validez",
    'Dans le menu gauche, cliquez "Bot"',
    'Cliquez "Add Bot" puis "Yes, do it!"',
    'Sous "Token", cliquez "Copy" pour copier votre token',
    'Activez "Message Content Intent" en dessous',
    "Invitez le bot sur votre serveur via OAuth2 → Bot",
  ];
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl border border-neutral-800 bg-neutral-900 p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Comment créer un bot Discord ?</h3>
          <button onClick={onClose} className="text-neutral-400 hover:text-white text-xl">×</button>
        </div>
        <ol className="space-y-3 text-sm text-neutral-300">
          {steps.map((s, i) => (
            <li key={i} className="flex gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
                {i + 1}
              </span>
              <span className="mt-0.5">{s}</span>
            </li>
          ))}
        </ol>
        <button
          onClick={onClose}
          className="mt-6 w-full rounded-xl bg-neutral-800 py-2.5 text-sm font-semibold text-white hover:bg-neutral-700 transition-colors"
        >
          J'ai compris
        </button>
      </div>
    </div>
  );
}

/* ─── PAGE ─── */
export default function NewBotPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const krBalance = session?.user?.kronesBalance ?? 0;

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [botName, setBotName] = useState("");
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [serviceMsg, setServiceMsg] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [modules, setModules] = useState<ModuleDef[]>(fallbackModules);
  const [apiLoading, setApiLoading] = useState(false);

  useEffect(() => {
    if (step === 2) {
      setApiLoading(true);
      fetch("/api/commands")
        .then((r) => r.json())
        .then((data: ApiCommand[]) => {
          if (!Array.isArray(data) || data.length === 0) return;

          // Grouper par category
          const grouped = new Map<string, ApiCommand[]>();
          for (const cmd of data) {
            const cat = cmd.category;
            if (!grouped.has(cat)) grouped.set(cat, []);
            grouped.get(cat)!.push(cmd);
          }

          const built: ModuleDef[] = [];
          for (const [cat, cmds] of grouped) {
            if (cmds.length === 1 && cmds[0].id === cmds[0].module) {
              // Module entier (flatPrice)
              built.push({
                id: cmds[0].module,
                name: cat,
                commands: [],
                flatPrice: cmds[0].priceKr,
              });
            } else {
              // Module avec commandes individuelles
              built.push({
                id: cmds[0].module,
                name: cat,
                commands: cmds.map((c) => ({ id: c.id, name: c.name, price: c.priceKr })),
              });
            }
          }

          setModules(built);
        })
        .catch(() => {
          // Utilise fallbackModules (déjà dans l'état)
        })
        .finally(() => setApiLoading(false));
    }
  }, [step]);

  const activeModules = modules;

  const totalCost = [...selected].reduce((sum, id) => {
    for (const mod of activeModules) {
      if (mod.flatPrice && id === mod.id) return sum + mod.flatPrice;
      const cmd = mod.commands.find((c) => c.id === id);
      if (cmd) return sum + cmd.price;
    }
    return sum;
  }, 0);

  const hasEnough = totalCost <= krBalance;

  function toggleModule(modId: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(modId)) next.delete(modId);
      else next.add(modId);
      return next;
    });
  }

  function toggleCommand(cmdId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(cmdId)) next.delete(cmdId);
      else next.add(cmdId);
      return next;
    });
  }

  function toggleFlatModule(modId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(modId)) next.delete(modId);
      else next.add(modId);
      return next;
    });
  }

  function canProceedStep1() {
    return botName.trim().length > 0 && botName.length <= 50 && token.trim().length > 0;
  }

  /* ── STEP 1 ── */
  if (step === 1) {
    return (
      <div className="p-8 max-w-2xl">
        <h1 className="text-2xl font-bold text-white mb-2">Créer un bot Discord</h1>
        <p className="text-neutral-400 text-sm mb-8">Étape 1 sur 3 — Token & Nom</p>

        <div className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Nom du bot *</label>
            <input
              type="text"
              value={botName}
              onChange={(e) => setBotName(e.target.value)}
              maxLength={50}
              placeholder="MonSuperBot"
              className="w-full rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white placeholder-neutral-600 focus:border-indigo-500 focus:outline-none"
            />
            <p className="mt-1 text-xs text-neutral-500">{botName.length}/50 caractères</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-1.5">Token Discord *</label>
            <div className="relative">
              <input
                type={showToken ? "text" : "password"}
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="MTA5ODc2NTQzMjEwOTg3NjU0MzIx.MTA5OA..."
                className="w-full rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 pr-10 text-sm text-white placeholder-neutral-600 focus:border-indigo-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => setShowToken((s) => !s)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 text-xs"
              >
                {showToken ? "Masquer" : "Afficher"}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          <button
            onClick={() => setHelpOpen(true)}
            className="rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2 text-sm text-neutral-300 hover:border-indigo-500/30 hover:text-white transition-colors"
          >
            Comment créer un bot Discord ?
          </button>
          <button
            onClick={() => {
              setServiceMsg("Service non disponible pour le moment");
              setTimeout(() => setServiceMsg(null), 3000);
            }}
            className="rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2 text-sm text-neutral-300 hover:border-yellow-500/30 hover:text-yellow-400 transition-colors"
          >
            Me le faire faire (3 Kr)
          </button>
        </div>

        {serviceMsg && (
          <p className="mt-3 text-sm text-yellow-400">{serviceMsg}</p>
        )}

        <div className="mt-8 flex justify-end">
          <button
            onClick={() => canProceedStep1() && setStep(2)}
            disabled={!canProceedStep1()}
            className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Suivant
          </button>
        </div>

        <HelpModal open={helpOpen} onClose={() => setHelpOpen(false)} />
      </div>
    );
  }

  /* ── STEP 2 ── */
  if (step === 2) {
    return (
      <div className="p-8 max-w-5xl pb-32">
        <h1 className="text-2xl font-bold text-white mb-2">Créer un bot Discord</h1>
        <p className="text-neutral-400 text-sm mb-8">Étape 2 sur 3 — Sélection des modules</p>

        {apiLoading && (
          <div className="text-center py-8">
            <span className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
            <p className="mt-2 text-sm text-neutral-400">Chargement des modules...</p>
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {activeModules.map((mod) => {
            const isExpanded = expanded.has(mod.id);
            const isFlatSelected = mod.flatPrice ? selected.has(mod.id) : false;
            const hasCommands = mod.commands.length > 0;

            return (
              <div
                key={mod.id}
                className={`rounded-xl border p-5 transition-colors ${
                  isExpanded || isFlatSelected
                    ? "border-indigo-500/30 bg-neutral-900"
                    : "border-neutral-800 bg-neutral-900/50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-white">{mod.name}</h3>
                  {mod.flatPrice ? (
                    <button
                      onClick={() => toggleFlatModule(mod.id)}
                      className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${
                        isFlatSelected
                          ? "bg-indigo-600 text-white"
                          : "bg-neutral-800 text-neutral-300 hover:bg-neutral-700"
                      }`}
                    >
                      {isFlatSelected ? "Sélectionné" : `+ ${mod.flatPrice} Kr`}
                    </button>
                  ) : (
                    <button
                      onClick={() => toggleModule(mod.id)}
                      className="rounded-lg bg-neutral-800 px-3 py-1 text-xs font-medium text-neutral-300 hover:bg-neutral-700 transition-colors"
                    >
                      {isExpanded ? "Fermer" : "Voir les commandes"}
                    </button>
                  )}
                </div>

                {hasCommands && isExpanded && (
                  <div className="mt-4 space-y-2">
                    {mod.commands.map((cmd) => {
                      const checked = selected.has(cmd.id);
                      return (
                        <label
                          key={cmd.id}
                          className={`flex cursor-pointer items-center justify-between rounded-lg border px-3 py-2 transition-colors ${
                            checked
                              ? "border-indigo-500/30 bg-indigo-500/10"
                              : "border-neutral-800 bg-neutral-900 hover:border-neutral-700"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleCommand(cmd.id)}
                              className="h-4 w-4 accent-indigo-500"
                            />
                            <span className="text-sm text-white">{cmd.name}</span>
                          </div>
                          <span className="text-xs text-neutral-400">{cmd.price} Kr</span>
                        </label>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Barre sticky récap */}
        <div className="fixed bottom-0 left-60 right-0 border-t border-neutral-800 bg-neutral-900/95 backdrop-blur px-8 py-4 z-40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6 text-sm">
              <span className="text-neutral-400">
                <span className="font-semibold text-white">{selected.size}</span> commandes sélectionnées
              </span>
              <span className="text-neutral-400">
                Coût total :{" "}
                <span className={`font-semibold ${hasEnough ? "text-white" : "text-red-400"}`}>
                  <KrBadge amount={totalCost} />
                </span>
              </span>
              <span className="text-neutral-400">
                Solde disponible :{" "}
                <KrBadge amount={krBalance} />
              </span>
              {!hasEnough && (
                <span className="text-sm font-medium text-red-400">Solde insuffisant</span>
              )}
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setStep(1)}
                className="rounded-xl border border-neutral-800 bg-neutral-900 px-5 py-2 text-sm font-medium text-neutral-300 hover:bg-neutral-800 transition-colors"
              >
                Retour
              </button>
              <button
                onClick={() => hasEnough && setStep(3)}
                disabled={!hasEnough}
                className="rounded-xl bg-indigo-600 px-6 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Suivant
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* ── STEP 3 ── */
  const afterBalance = krBalance - totalCost;
  const selectedItems = [...selected].map((id) => {
    for (const mod of activeModules) {
      if (mod.flatPrice && id === mod.id) return { name: mod.name, price: mod.flatPrice };
      const cmd = mod.commands.find((c) => c.id === id);
      if (cmd) return { name: `${mod.name.toLowerCase()}.${cmd.name}`, price: cmd.price };
    }
    return { name: id, price: 0 };
  });

  async function handleCreate() {
    if (!hasEnough) return;
    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch("/api/bots/provision", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          botName: botName.trim(),
          botToken: token.trim(),
          prefix: "!",
          cogs: [...selected],
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setErrorMsg(data.error ?? "Une erreur est survenue");
        setLoading(false);
        return;
      }

      router.push(`/dashboard/bots/${data.botId}`);
    } catch {
      setErrorMsg("Erreur réseau. Réessayez.");
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-3xl pb-28">
      <h1 className="text-2xl font-bold text-white mb-2">Créer un bot Discord</h1>
      <p className="text-neutral-400 text-sm mb-8">Étape 3 sur 3 — Récapitulatif &amp; Lancement</p>

      {/* Tableau récap */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 bg-neutral-900/80 text-left">
              <th className="px-5 py-3 font-medium text-neutral-400">Module / Commande</th>
              <th className="px-5 py-3 font-medium text-neutral-400 text-right">Coût</th>
            </tr>
          </thead>
          <tbody>
            {selectedItems.map((item, i) => (
              <tr key={i} className="border-b border-neutral-800/50">
                <td className="px-5 py-3 text-white">{item.name}</td>
                <td className="px-5 py-3 text-right text-neutral-300">{item.price} Kr</td>
              </tr>
            ))}
            <tr className="bg-neutral-900/60">
              <td className="px-5 py-3 font-semibold text-white">Total</td>
              <td className="px-5 py-3 text-right font-bold text-white"><KrBadge amount={totalCost} /></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Solde */}
      <div className="mt-6 rounded-xl border border-neutral-800 bg-neutral-900 p-5">
        <div className="flex flex-col gap-2 text-sm">
          <div className="flex justify-between">
            <span className="text-neutral-400">Solde avant</span>
            <KrBadge amount={krBalance} />
          </div>
          <div className="flex justify-between">
            <span className="text-neutral-400">Coût total</span>
            <span className="font-medium text-red-400">- <KrBadge amount={totalCost} /></span>
          </div>
          <div className="flex justify-between border-t border-neutral-800 pt-2 mt-1">
            <span className="text-neutral-400">Solde après</span>
            <KrBadge amount={afterBalance} />
          </div>
        </div>
      </div>

      {/* Erreur */}
      {errorMsg && (
        <div className="mt-4 rounded-xl border border-red-500/20 bg-red-500/10 px-5 py-3 text-sm text-red-400">
          {errorMsg}
        </div>
      )}

      {/* Boutons */}
      <div className="mt-8 flex items-center justify-between">
        <button
          onClick={() => setStep(2)}
          className="rounded-xl border border-neutral-800 bg-neutral-900 px-5 py-2.5 text-sm font-medium text-neutral-300 hover:bg-neutral-800 transition-colors"
        >
          Retour
        </button>
        {!hasEnough ? (
          <div className="flex flex-col items-end gap-2">
            <p className="text-sm text-red-400">Solde insuffisant pour déployer ce bot</p>
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
            Déploiement en cours...
          </div>
        ) : (
          <button
            onClick={handleCreate}
            className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
          >
            Créer mon bot
          </button>
        )}
      </div>
    </div>
  );
}
