"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { StatusBadge } from "@/components/ui/StatusBadge";

type MinecraftServer = {
  id: string;
  serverName: string;
  version: string;
  ramMb: number;
  status: string;
};

export default function MinecraftPage() {
  const [servers, setServers] = useState<MinecraftServer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/user/services")
      .then((r) => r.json())
      .then((data) => {
        setServers(data.minecraftServers ?? []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-neutral-400">Chargement...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Mes Serveurs Minecraft</h1>
        <Link
          href="/dashboard/minecraft/new"
          className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-emerald-500"
        >
          + Créer un serveur Minecraft
        </Link>
      </div>

      {servers.length === 0 ? (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-8 text-center">
          <p className="text-neutral-400">Vous n'avez pas encore de serveurs Minecraft.</p>
          <Link
            href="/dashboard/minecraft/new"
            className="mt-4 inline-block rounded-xl bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-500"
          >
            Créer mon premier serveur
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {servers.map((server) => (
            <div key={server.id} className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white truncate">{server.serverName}</h3>
                <StatusBadge status={server.status as any} />
              </div>
              <div className="flex items-center gap-4 text-sm text-neutral-400">
                <span>{server.version}</span>
                <span>{Math.round(server.ramMb / 1024)} Go RAM</span>
              </div>
              <Link
                href={`/dashboard/minecraft/${server.id}`}
                className="mt-auto w-full rounded-lg bg-neutral-800 px-4 py-2 text-center text-sm font-medium text-white transition-colors hover:bg-neutral-700"
              >
                Gérer
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
