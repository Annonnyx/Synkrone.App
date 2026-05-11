"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { RoleBadge } from "@/components/ui/RoleBadge";
import { KrBadge } from "@/components/ui/KrBadge";

type User = {
  id: string;
  discordId: string;
  username: string;
  avatar: string | null;
  roles: string[];
  kronesBalance: number;
  kronesSpent: number;
  subscription: { plan: string } | null;
  totalServices: number;
  createdAt: string;
};

export default function AdminUsersPage() {
  const { data: session } = useSession();
  const userRoles = session?.user?.roles ?? [];
  const isSupervisor = userRoles.some((r) => ["SUPERVISOR", "LEADER"].includes(r));

  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [modalUser, setModalUser] = useState<User | null>(null);
  const [krAmount, setKrAmount] = useState("");
  const [krReason, setKrReason] = useState("");
  const [krLoading, setKrLoading] = useState(false);

  useEffect(() => {
    fetch("/api/admin/users")
      .then((r) => r.json())
      .then((data: User[]) => {
        setUsers(data);
        setLoading(false);
      })
      .catch(() => {
        setError("Erreur de chargement");
        setLoading(false);
      });
  }, []);

  async function handleGrantKr() {
    if (!modalUser || !krAmount || !krReason) return;
    setKrLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/admin/users/${modalUser.id}/krones`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: Number(krAmount), reason: krReason }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur");
      } else {
        setModalOpen(false);
        setKrAmount("");
        setKrReason("");
        // Recharger
        const refresh = await fetch("/api/admin/users");
        setUsers(await refresh.json());
      }
    } catch {
      setError("Erreur réseau");
    } finally {
      setKrLoading(false);
    }
  }

  async function handleSuspend(userId: string) {
    if (!confirm("Suspendre cet utilisateur ?")) return;
    // TODO: implémenter l'API de suspension
    alert("API de suspension non encore implémentée");
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
      <h1 className="text-2xl font-bold text-white">Utilisateurs</h1>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Modal Gérer Kr */}
      {modalOpen && modalUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl border border-neutral-800 bg-neutral-900 p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-4">Gérer les Krônes — {modalUser.username}</h3>
            <p className="text-sm text-neutral-400 mb-4">
              Solde actuel : <KrBadge amount={modalUser.kronesBalance} />
            </p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-neutral-300 mb-1">Montant (positif = crédit, négatif = débit)</label>
                <input
                  type="number"
                  value={krAmount}
                  onChange={(e) => setKrAmount(e.target.value)}
                  className="w-full rounded-xl border border-neutral-800 bg-neutral-950 px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm text-neutral-300 mb-1">Raison</label>
                <input
                  type="text"
                  value={krReason}
                  onChange={(e) => setKrReason(e.target.value)}
                  className="w-full rounded-xl border border-neutral-800 bg-neutral-950 px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none"
                />
              </div>
            </div>
            <div className="mt-6 flex gap-3">
              <button
                onClick={() => setModalOpen(false)}
                className="flex-1 rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm font-medium text-neutral-300 hover:bg-neutral-800 transition-colors"
              >
                Annuler
              </button>
              <button
                onClick={handleGrantKr}
                disabled={krLoading || !krAmount || !krReason}
                className="flex-1 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-40"
              >
                {krLoading ? "..." : "Confirmer"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 bg-neutral-900/80 text-left">
              <th className="px-4 py-3 font-medium text-neutral-400">Avatar</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Pseudo</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Rôle</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Solde Kr</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Abonnement</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Services</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Inscription</th>
              <th className="px-4 py-3 font-medium text-neutral-400 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-neutral-800/50">
                <td className="px-4 py-3">
                  {u.avatar ? (
                    <img src={u.avatar} alt={u.username} className="h-8 w-8 rounded-full bg-neutral-800" />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-neutral-800 flex items-center justify-center text-xs font-bold">
                      {u.username?.charAt(0) ?? "?"}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3 text-white font-medium">{u.username}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {u.roles.map((r) => (
                      <RoleBadge key={r} role={r} />
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3"><KrBadge amount={u.kronesBalance} /></td>
                <td className="px-4 py-3 text-neutral-300">
                  {u.subscription?.plan ?? "—"}
                </td>
                <td className="px-4 py-3 text-neutral-300">{u.totalServices}</td>
                <td className="px-4 py-3 text-neutral-400 text-xs">
                  {new Date(u.createdAt).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" })}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex gap-2 justify-end">
                    <Link
                      href={`/dashboard/bots`}
                      className="text-xs text-cyan-400 hover:underline"
                    >
                      Voir les services
                    </Link>
                    <button
                      onClick={() => { setModalUser(u); setModalOpen(true); }}
                      className="text-xs text-indigo-400 hover:underline"
                    >
                      Gérer Kr
                    </button>
                    {isSupervisor && (
                      <button
                        onClick={() => handleSuspend(u.id)}
                        className="text-xs text-red-400 hover:underline"
                      >
                        Suspendre
                      </button>
                    )}
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
