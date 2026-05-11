"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Folder,
  FileText,
  Image,
  Film,
  Music,
  Archive,
  Code,
  File,
  ChevronRight,
  Home,
  Plus,
  Upload,
  Trash2,
  RefreshCw,
  FolderPlus,
  X,
  HardDrive,
  ArrowUp,
} from "lucide-react";

interface FileItem {
  name: string;
  type: "file" | "directory";
  size: number;
  mtime: string;
}

interface FileManagerProps {
  userId: string;
  username: string;
}

function formatSize(bytes: number): string {
  if (bytes === 0) return "—";
  const units = ["o", "Ko", "Mo", "Go"];
  let i = 0;
  let b = bytes;
  while (b >= 1024 && i < units.length - 1) {
    b /= 1024;
    i++;
  }
  return `${b.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function getFileIcon(name: string, type: string) {
  if (type === "directory") return <Folder className="h-5 w-5 text-amber-400" />;
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  if (["jpg", "jpeg", "png", "gif", "webp", "svg", "ico"].includes(ext))
    return <Image className="h-5 w-5 text-purple-400" />;
  if (["mp4", "mov", "avi", "mkv", "webm"].includes(ext))
    return <Film className="h-5 w-5 text-rose-400" />;
  if (["mp3", "wav", "ogg", "flac", "aac"].includes(ext))
    return <Music className="h-5 w-5 text-emerald-400" />;
  if (["zip", "tar", "gz", "rar", "7z"].includes(ext))
    return <Archive className="h-5 w-5 text-orange-400" />;
  if (["js", "ts", "jsx", "tsx", "py", "java", "cpp", "c", "go", "rs", "php", "html", "css", "json", "sql", "prisma"].includes(ext))
    return <Code className="h-5 w-5 text-cyan-400" />;
  if (["txt", "md", "log", "csv"].includes(ext))
    return <FileText className="h-5 w-5 text-neutral-300" />;
  return <File className="h-5 w-5 text-neutral-400" />;
}

function getBreadcrumbs(currentPath: string): string[] {
  if (!currentPath) return [];
  return currentPath.split("/").filter(Boolean);
}

export default function FileManager({ userId, username }: FileManagerProps) {
  const [items, setItems] = useState<FileItem[]>([]);
  const [currentPath, setCurrentPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalSize, setTotalSize] = useState(0);
  const [newFolderName, setNewFolderName] = useState("");
  const [showMkdir, setShowMkdir] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/admin/boxes/browse?userId=${encodeURIComponent(userId)}&path=${encodeURIComponent(currentPath)}`
      );
      const data = await res.json();
      if (res.ok) {
        setItems(data.items ?? []);
        setTotalSize(data.totalSize ?? 0);
      } else {
        setError(data.error ?? "Erreur de chargement");
      }
    } catch {
      setError("Erreur réseau");
    } finally {
      setLoading(false);
    }
  }, [userId, currentPath]);

  useEffect(() => {
    if (userId) fetchItems();
  }, [fetchItems, userId]);

  async function handleMkdir() {
    if (!newFolderName.trim()) return;
    setError(null);
    try {
      const res = await fetch("/api/admin/boxes/browse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, path: currentPath, name: newFolderName.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur lors de la création");
      } else {
        setNewFolderName("");
        setShowMkdir(false);
        fetchItems();
      }
    } catch {
      setError("Erreur réseau");
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(
        `/api/admin/boxes/browse?userId=${encodeURIComponent(userId)}&path=${encodeURIComponent(currentPath)}`,
        { method: "POST", body: formData }
      );
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur lors de l'upload");
      } else {
        fetchItems();
      }
    } catch {
      setError("Erreur réseau lors de l'upload");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete(item: FileItem) {
    if (!confirm(`Supprimer "${item.name}" ?`)) return;
    setError(null);
    try {
      const relativePath = currentPath ? `${currentPath}/${item.name}` : item.name;
      const res = await fetch("/api/admin/boxes/browse", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, path: relativePath }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Erreur lors de la suppression");
      } else {
        fetchItems();
      }
    } catch {
      setError("Erreur réseau");
    }
  }

  function handleItemClick(item: FileItem) {
    if (item.type === "directory") {
      setCurrentPath((prev) => (prev ? `${prev}/${item.name}` : item.name));
    }
  }

  function navigateToBreadcrumb(index: number) {
    const crumbs = getBreadcrumbs(currentPath);
    const newPath = crumbs.slice(0, index + 1).join("/");
    setCurrentPath(newPath);
  }

  function navigateUp() {
    const crumbs = getBreadcrumbs(currentPath);
    crumbs.pop();
    setCurrentPath(crumbs.join("/"));
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-neutral-400">
          <HardDrive className="h-4 w-4" />
          <span>Box de {username}</span>
          <span className="text-neutral-600">|</span>
          <span>{formatSize(totalSize)} utilisé</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowMkdir(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-neutral-300 transition-all hover:bg-white/[0.06]"
          >
            <FolderPlus className="h-3.5 w-3.5" />
            Nouveau dossier
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-cyan-600 px-3 py-1.5 text-xs font-medium text-white transition-all hover:bg-cyan-500 disabled:opacity-50"
          >
            <Upload className="h-3.5 w-3.5" />
            {uploading ? "Upload…" : "Upload"}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleUpload}
            className="hidden"
          />
          <button
            onClick={fetchItems}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-neutral-300 transition-all hover:bg-white/[0.06] disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Actualiser
          </button>
        </div>
      </div>

      {/* Breadcrumbs */}
      <div className="flex items-center gap-1 text-sm">
        <button
          onClick={() => setCurrentPath("")}
          className="inline-flex items-center gap-1 text-neutral-400 hover:text-white transition-colors"
        >
          <Home className="h-3.5 w-3.5" />
          Racine
        </button>
        {getBreadcrumbs(currentPath).map((crumb, i) => (
          <span key={i} className="flex items-center gap-1 text-neutral-500">
            <ChevronRight className="h-3 w-3" />
            <button
              onClick={() => navigateToBreadcrumb(i)}
              className="text-neutral-400 hover:text-white transition-colors"
            >
              {crumb}
            </button>
          </span>
        ))}
        {currentPath && (
          <button
            onClick={navigateUp}
            className="ml-2 inline-flex items-center gap-1 rounded border border-white/[0.06] bg-white/[0.02] px-2 py-0.5 text-xs text-neutral-400 hover:text-white transition-colors"
          >
            <ArrowUp className="h-3 w-3" />
            Remonter
          </button>
        )}
      </div>

      {/* New folder input */}
      {showMkdir && (
        <div className="flex items-center gap-2 rounded-lg border border-cyan-500/20 bg-cyan-500/5 px-3 py-2">
          <FolderPlus className="h-4 w-4 text-cyan-400" />
          <input
            autoFocus
            type="text"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleMkdir()}
            placeholder="Nom du dossier"
            className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-neutral-500"
          />
          <button
            onClick={handleMkdir}
            className="rounded bg-cyan-600 px-2 py-1 text-xs font-medium text-white hover:bg-cyan-500"
          >
            Créer
          </button>
          <button
            onClick={() => { setShowMkdir(false); setNewFolderName(""); }}
            className="rounded p-1 text-neutral-400 hover:text-white"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* File list */}
      <div className="flex-1 rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800 bg-neutral-900/80 text-left">
              <th className="px-4 py-2.5 font-medium text-neutral-400">Nom</th>
              <th className="px-4 py-2.5 font-medium text-neutral-400">Taille</th>
              <th className="px-4 py-2.5 font-medium text-neutral-400">Modifié</th>
              <th className="px-4 py-2.5 font-medium text-neutral-400 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-neutral-400 text-xs">
                  Chargement…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-neutral-500 text-xs">
                  Ce dossier est vide.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr
                  key={item.name}
                  className="border-b border-neutral-800/40 hover:bg-white/[0.02] transition-colors"
                >
                  <td className="px-4 py-2">
                    <button
                      onClick={() => handleItemClick(item)}
                      className="flex items-center gap-2 text-white hover:text-cyan-300 transition-colors"
                    >
                      {getFileIcon(item.name, item.type)}
                      <span className="truncate max-w-xs">{item.name}</span>
                    </button>
                  </td>
                  <td className="px-4 py-2 text-neutral-300 text-xs">
                    {formatSize(item.size)}
                  </td>
                  <td className="px-4 py-2 text-neutral-400 text-xs whitespace-nowrap">
                    {new Date(item.mtime).toLocaleDateString("fr-FR", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => handleDelete(item)}
                      className="rounded p-1 text-neutral-500 hover:text-red-400 transition-colors"
                      title="Supprimer"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
