"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { Package, HardDrive } from "lucide-react";

type User = {
  id: string;
  username: string;
  avatar: string | null;
  boxQuotaMb: number;
  roles: string[];
};

export default function AdminBoxesPage() {
  const { data: session } = useSession();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-neutral-400">Chargement...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl space-y-6">
      <div className="flex items-center gap-3">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-orange-500/10 text-orange-400">
          <HardDrive className="h-6 w-6" />
        </div>
        <h1 className="text-2xl font-bold text-white">Toutes les Boxes</h1>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 bg-neutral-900/80 text-left">
              <th className="px-4 py-3 font-medium text-neutral-400">Utilisateur</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Rôles</th>
              <th className="px-4 py-3 font-medium text-neutral-400">Quota Box</th>
              <th className="px-4 py-3 font-medium text-neutral-400 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-neutral-800/50">
                <td className="px-4 py-3 flex items-center gap-3">
                  {u.avatar ? (
                    <img src={u.avatar} alt={u.username} className="h-8 w-8 rounded-full bg-neutral-800" />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-neutral-800 flex items-center justify-center text-xs font-bold">
                      {u.username?.charAt(0) ?? "?"}
                    </div>
                  )}
                  <span className="text-white font-medium">{u.username}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {u.roles.map((r) => (
                      <span
                        key={r}
                        className="inline-flex rounded-full bg-neutral-800 px-2 py-0.5 text-xs text-neutral-300"
                      >
                        {r}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-neutral-300">
                  {u.boxQuotaMb === -1 || u.boxQuotaMb === 99999
                    ? "Illimité"
                    : `${u.boxQuotaMb.toLocaleString("fr-FR")} Mo`}
                </td>
                <td className="px-4 py-3 text-right">
                  <a
                    href={`/dev/boxes/${u.id}`}
                    className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:underline"
                  >
                    <Package className="h-3 w-3" />
                    Ouvrir
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
