"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { HardDrive, FolderOpen, ChevronLeft } from "lucide-react";
import FileManager from "@/components/dev/FileManager";

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
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

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

  if (selectedUser) {
    return (
      <div className="p-8 h-[calc(100vh-4rem)] flex flex-col">
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={() => setSelectedUser(null)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-neutral-300 transition-all hover:bg-white/[0.06]"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Retour à la liste
          </button>
        </div>
        <div className="flex-1 min-h-0">
          <FileManager userId={selectedUser.id} username={selectedUser.username} />
        </div>
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
                  <button
                    onClick={() => setSelectedUser(u)}
                    className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                  >
                    <FolderOpen className="h-3 w-3" />
                    Ouvrir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
