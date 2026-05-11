"use client";

import { useSession } from "next-auth/react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { hasRole, ROLE_HIERARCHY, type Role, BOX_SIZE_BY_ROLE } from "@/lib/roles";
import { RoleBadge } from "@/components/ui/RoleBadge";
import { Package, FolderOpen, Users, Bot, LayoutGrid, Monitor } from "lucide-react";

export default function DevPage() {
  const { data: session } = useSession();
  const user = session?.user;
  const username = user?.name ?? "développeur";
  const roles = user?.roles ?? ["USER"];
  const topRole = roles.reduce<Role>((highest, r) => {
    const rIdx = ROLE_HIERARCHY.indexOf(r as Role);
    const hIdx = ROLE_HIERARCHY.indexOf(highest);
    return rIdx > hIdx ? (r as Role) : highest;
  }, "USER");

  const [boxInfo, setBoxInfo] = useState<{ quota: number; used: number } | null>(null);
  const [boxLoading, setBoxLoading] = useState(true);

  useEffect(() => {
    if (user?.dbId) {
      fetch("/api/krones/balance")
        .then((r) => r.json())
        .then(() => {
          // Simuler les infos de box depuis l'API user/me
          return fetch("/api/user/me");
        })
        .then((r) => r.json())
        .then((data: { boxQuotaMb: number; boxUsedMb?: number }) => {
          const quota = data.boxQuotaMb;
          // Used = récupéré depuis l'API (0 par défaut si endpoint box absent)
          const used = data.boxUsedMb ?? 0;
          setBoxInfo({ quota, used });
          setBoxLoading(false);
        })
        .catch(() => {
          // Fallback : utiliser le quota du rôle
          const quota = BOX_SIZE_BY_ROLE[topRole];
          setBoxInfo({ quota: quota === -1 ? 99999 : quota, used: 0 });
          setBoxLoading(false);
        });
    }
  }, [user?.dbId, topRole]);

  const isManagerOrAbove = hasRole(roles, "MANAGER");
  const isSupervisorOrAbove = hasRole(roles, "SUPERVISOR");
  const isLeader = hasRole(roles, "LEADER");

  const boxQuota = boxInfo?.quota ?? BOX_SIZE_BY_ROLE[topRole];
  const boxUsed = boxInfo?.used ?? 0;
  const boxAvailable = boxQuota === -1 ? "∞" : (boxQuota - boxUsed).toLocaleString("fr-FR");
  const boxPct = boxQuota === -1 ? 0 : Math.min((boxUsed / boxQuota) * 100, 100);

  return (
    <div className="p-8 max-w-5xl space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">
            Bonjour {username} <span className="text-cyan-400">— Espace développeur</span>
          </h1>
          <div className="mt-2 flex items-center gap-2">
            <RoleBadge role={topRole} />
            {roles.length > 1 && (
              <span className="text-xs text-neutral-500">({roles.length} rôles)</span>
            )}
          </div>
        </div>
      </div>

      {/* Box info */}
      <div className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Ma Box</h2>
        {boxLoading ? (
          <p className="text-sm text-neutral-500">Chargement...</p>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-6">
              <div className="text-center">
                <p className="text-2xl font-extrabold text-white">{boxQuota === -1 ? "∞" : boxQuota.toLocaleString("fr-FR")} <span className="text-sm font-normal text-neutral-400">Mo</span></p>
                <p className="text-xs text-neutral-500">Quota</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-extrabold text-cyan-400">{boxUsed.toLocaleString("fr-FR")} <span className="text-sm font-normal text-neutral-400">Mo</span></p>
                <p className="text-xs text-neutral-500">Utilisé</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-extrabold text-emerald-400">{boxAvailable} <span className="text-sm font-normal text-neutral-400">Mo</span></p>
                <p className="text-xs text-neutral-500">Disponible</p>
              </div>
            </div>
            <div className="h-3 w-full rounded-full bg-neutral-800 overflow-hidden">
              <div className="h-full rounded-full bg-cyan-500 transition-all" style={{ width: `${boxPct}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* Raccourcis */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Accès rapide</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Link
            href="/dev/boxes"
            className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 transition-colors hover:border-cyan-500/30 hover:bg-neutral-800"
          >
            <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400"><Package className="h-6 w-6" /></div>
            <h3 className="font-semibold text-white">Ma Box</h3>
            <p className="mt-1 text-sm text-neutral-500">Gérez vos fichiers et déploiements</p>
          </Link>
          <Link
            href="/dev/boxes/shared"
            className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 transition-colors hover:border-cyan-500/30 hover:bg-neutral-800"
          >
            <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400"><FolderOpen className="h-6 w-6" /></div>
            <h3 className="font-semibold text-white">Box Partagée</h3>
            <p className="mt-1 text-sm text-neutral-500">Fichiers partagés avec l'équipe</p>
          </Link>
          {isManagerOrAbove && (
            <Link
              href="/dev/admin/users"
              className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 transition-colors hover:border-amber-500/30 hover:bg-neutral-800"
            >
              <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400"><Users className="h-6 w-6" /></div>
              <h3 className="font-semibold text-white">Utilisateurs</h3>
              <p className="mt-1 text-sm text-neutral-500">Gérer les membres et rôles</p>
            </Link>
          )}
          {isManagerOrAbove && (
            <Link
              href="/dev/admin/bots"
              className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 transition-colors hover:border-amber-500/30 hover:bg-neutral-800"
            >
              <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400"><Bot className="h-6 w-6" /></div>
              <h3 className="font-semibold text-white">Tous les Bots</h3>
              <p className="mt-1 text-sm text-neutral-500">Supervision des bots Discord</p>
            </Link>
          )}
          {isSupervisorOrAbove && (
            <Link
              href="/dev/admin/boxes"
              className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 transition-colors hover:border-orange-500/30 hover:bg-neutral-800"
            >
              <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-orange-500/10 text-orange-400"><LayoutGrid className="h-6 w-6" /></div>
              <h3 className="font-semibold text-white">Toutes les Boxes</h3>
              <p className="mt-1 text-sm text-neutral-500">Gestion du stockage global</p>
            </Link>
          )}
          {isLeader && (
            <Link
              href="/dev/admin/terminal"
              className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 transition-colors hover:border-rose-500/30 hover:bg-neutral-800"
            >
              <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-rose-500/10 text-rose-400"><Monitor className="h-6 w-6" /></div>
              <h3 className="font-semibold text-white">Terminal VPS</h3>
              <p className="mt-1 text-sm text-neutral-500">Accès SSH au serveur</p>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
