"use client";

import { useState, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";

interface BoxFile {
  name: string;
  size: number;
  mtime: string;
  owner?: string;
}

const TOTAL_QUOTA_MB = 20 * 1024; // 20 Go

function formatSize(bytes: number): string {
  const units = ["o", "Ko", "Mo", "Go"];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024;
    i++;
  }
  return `${bytes.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export default function SharedBoxPage() {
  const { data: session } = useSession();
  const username = session?.user?.name ?? "Anonyme";
  const [files, setFiles] = useState<BoxFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [quotaUsed, setQuotaUsed] = useState(0);

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/dev/boxes/shared");
      const data = await res.json();
      if (res.ok) {
        setFiles(data.files ?? []);
        setQuotaUsed(data.totalSize ?? 0);
      } else {
        setError(data.error ?? "Erreur de chargement");
      }
    } catch {
      setError("Erreur réseau");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/dev/boxes/shared/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur lors de l'upload");
      } else {
        setSuccessMsg(`"${file.name}" uploadé avec succès`);
        setTimeout(() => setSuccessMsg(null), 3000);
        fetchFiles();
      }
    } catch {
      setError("Erreur réseau lors de l'upload");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleDelete(filename: string) {
    if (!confirm(`Supprimer "${filename}" ?`)) return;
    setError(null);
    try {
      const res = await fetch("/api/dev/boxes/shared", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur lors de la suppression");
      } else {
        setSuccessMsg(`"${filename}" supprimé`);
        setTimeout(() => setSuccessMsg(null), 3000);
        fetchFiles();
      }
    } catch {
      setError("Erreur réseau");
    }
  }

  const quotaPct = Math.min((quotaUsed / TOTAL_QUOTA_MB) * 100, 100);

  return (
    <div className="p-8 max-w-5xl space-y-6">
      {/* En-tête */}
      <div>
        <h1 className="text-2xl font-bold text-white">Box Partagée</h1>
        <p className="text-cyan-400 text-sm mt-1">Accessible à toute l'équipe</p>
      </div>

      {/* Note */}
      <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 px-5 py-3 text-sm text-amber-300">
        Tout fichier déposé ici peut être modifié ou supprimé par n'importe quel membre de l'équipe.
      </div>

      {/* Quota */}
      <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
        <div className="flex items-center justify-between text-sm mb-2">
          <span className="text-neutral-400">Stockage utilisé</span>
          <span className="text-white font-medium">{formatSize(quotaUsed * 1024 * 1024)} / 20 Go</span>
        </div>
        <div className="h-2 w-full rounded-full bg-neutral-800 overflow-hidden">
          <div className="h-full rounded-full bg-cyan-500 transition-all" style={{ width: `${quotaPct}%` }} />
        </div>
      </div>

      {/* Upload */}
      <div className="flex items-center gap-4">
        <label className="relative cursor-pointer rounded-xl bg-cyan-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-cyan-500">
          {uploading ? "Upload en cours..." : "+ Upload un fichier"}
          <input
            type="file"
            onChange={handleUpload}
            disabled={uploading}
            className="absolute inset-0 cursor-pointer opacity-0"
          />
        </label>
      </div>

      {successMsg && (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-400">
          {successMsg}
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Liste */}
      {loading ? (
        <p className="text-neutral-400 text-sm">Chargement...</p>
      ) : files.length === 0 ? (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-8 text-center">
          <p className="text-neutral-400">Aucun fichier dans la box partagée.</p>
          <p className="mt-1 text-sm text-neutral-500">Soyez le premier à en ajouter un !</p>
        </div>
      ) : (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800 bg-neutral-900/80 text-left">
                <th className="px-5 py-3 font-medium text-neutral-400">Nom</th>
                <th className="px-5 py-3 font-medium text-neutral-400">Taille</th>
                <th className="px-5 py-3 font-medium text-neutral-400">Date</th>
                <th className="px-5 py-3 font-medium text-neutral-400">Uploadé par</th>
                <th className="px-5 py-3 font-medium text-neutral-400 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {files.map((f) => (
                <tr key={f.name} className="border-b border-neutral-800/50">
                  <td className="px-5 py-3 text-white truncate max-w-xs">{f.name}</td>
                  <td className="px-5 py-3 text-neutral-300">{formatSize(f.size)}</td>
                  <td className="px-5 py-3 text-neutral-300 whitespace-nowrap">
                    {new Date(f.mtime).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                  </td>
                  <td className="px-5 py-3">
                    {f.owner ? (
                      <span className="inline-flex rounded-full bg-neutral-800 px-2 py-0.5 text-xs text-neutral-300">
                        {f.owner}
                      </span>
                    ) : (
                      <span className="text-xs text-neutral-600">Inconnu</span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => handleDelete(f.name)}
                      className="text-xs text-red-400 hover:text-red-300 transition-colors"
                    >
                      Supprimer
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
