"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { KrBadge } from "@/components/ui/KrBadge";
import { Bot, Server, Globe, Smartphone } from "lucide-react";

interface Service {
  id: string;
  name: string;
  type: "bot" | "minecraft" | "site" | "app";
  status: string;
}

function ServiceIcon({ type }: { type: string }) {
  switch (type) {
    case "bot":
      return (
        <svg className="h-5 w-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-1.5a2.25 2.25 0 00-2.25-2.25H4.5a2.25 2.25 0 00-2.25 2.25v1.5a2.25 2.25 0 002.25 2.25z" />
        </svg>
      );
    case "minecraft":
      return (
        <svg className="h-5 w-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="m21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
        </svg>
      );
    case "site":
      return (
        <svg className="h-5 w-5 text-sky-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.162 0-4.215.633-5.91 1.64A11.95 11.95 0 012.343 7.5" />
        </svg>
      );
    case "app":
      return (
        <svg className="h-5 w-5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
        </svg>
      );
    default:
      return null;
  }
}

function getServiceLink(service: Service) {
  switch (service.type) {
    case "bot":
      return `/dashboard/bots/${service.id}`;
    case "minecraft":
      return `/dashboard/minecraft/${service.id}`;
    case "site":
      return `/dashboard/sites/${service.id}`;
    case "app":
      return `/dashboard/apps/${service.id}`;
    default:
      return "#";
  }
}

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const [services, setServices] = useState<Service[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const user = session?.user;
  const username = user?.name ?? "utilisateur";

  useEffect(() => {
    if (status === "authenticated") {
      Promise.all([
        fetch("/api/user/services").then((r) => r.json()),
        fetch("/api/user/stats").then((r) => r.json()),
      ])
        .then(([servicesData, statsData]) => {
          setServices(servicesData.services ?? []);
          setStats(statsData);
        })
        .catch(() => {
          setServices([]);
        })
        .finally(() => setLoading(false));
    } else if (status !== "loading") {
      setLoading(false);
    }
  }, [status]);

  const bots = services.filter((s) => s.type === "bot");
  const mcServers = services.filter((s) => s.type === "minecraft");
  const sites = services.filter((s) => s.type === "site");
  const apps = services.filter((s) => s.type === "app");
  const totalServices = services.length;

  return (
    <div className="p-8 max-w-6xl">
      {/* Titre */}
      <h1 className="text-3xl font-bold tracking-tight text-white">
        Bonjour, {username} 👋
      </h1>

      {/* Statuts */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
          <p className="text-sm text-neutral-400">Solde Kr</p>
          <p className="mt-1 text-2xl font-bold"><KrBadge amount={user?.kronesBalance ?? 0} /></p>
        </div>
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
          <p className="text-sm text-neutral-400">Kr dépensés ce mois</p>
          <p className="mt-1 text-2xl font-bold text-red-400">{stats?.krSpentMonth ?? 0} Kr</p>
        </div>
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
          <p className="text-sm text-neutral-400">Bots en ligne</p>
          <p className="mt-1 text-2xl font-bold text-white">{stats?.bots?.online ?? bots.filter((b) => b.status === "ONLINE").length} / {stats?.bots?.total ?? bots.length}</p>
        </div>
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-5">
          <p className="text-sm text-neutral-400">Serveurs MC en ligne</p>
          <p className="mt-1 text-2xl font-bold text-white">{stats?.minecraft?.online ?? mcServers.filter((s) => s.status === "ONLINE").length} / {stats?.minecraft?.total ?? mcServers.length}</p>
        </div>
      </div>

      {/* Stats enrichies */}
      {stats && (
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-4">
            <p className="text-xs text-neutral-500">Commandes utilisées (bots)</p>
            <p className="mt-1 text-xl font-bold text-white">{stats.bots?.commandsUsed ?? 0}</p>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-4">
            <p className="text-xs text-neutral-500">Kr gagnés ce mois</p>
            <p className="mt-1 text-xl font-bold text-emerald-400">+{stats.krEarnedMonth ?? 0} Kr</p>
          </div>
          <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-4">
            <p className="text-xs text-neutral-500">Transactions récentes</p>
            <p className="mt-1 text-xl font-bold text-white">{stats.transactions?.length ?? 0}</p>
          </div>
        </div>
      )}

      {/* Services actifs */}
      <div className="mt-10">
        <h2 className="text-xl font-semibold text-white">Mes services actifs</h2>

        {loading ? (
          <div className="mt-6 rounded-xl border border-neutral-800 bg-neutral-900 p-8 text-center text-neutral-400">
            Chargement...
          </div>
        ) : services.length === 0 ? (
          <div className="mt-6 rounded-xl border border-neutral-800 bg-neutral-900 p-8 text-center">
            <p className="text-neutral-400">Vous n'avez pas encore de services</p>
            <p className="mt-2 text-sm text-neutral-500">Commencez par créer votre premier service ci-dessous.</p>
          </div>
        ) : (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {services.map((service) => (
              <div
                key={service.id}
                className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 flex flex-col gap-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <ServiceIcon type={service.type} />
                    <span className="font-semibold text-white truncate">{service.name}</span>
                  </div>
                  <StatusBadge status={service.status as any} />
                </div>
                <Link
                  href={getServiceLink(service)}
                  className="mt-auto w-full rounded-lg bg-neutral-800 px-4 py-2 text-center text-sm font-medium text-white transition-colors hover:bg-neutral-700"
                >
                  Gérer
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Boutons de création */}
      <div className="mt-10">
        <h2 className="text-xl font-semibold text-white">Créer un service</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link
            href="/dashboard/bots/new"
            className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 text-center transition-colors hover:border-indigo-500/30 hover:bg-neutral-800"
          >
            <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400"><Bot className="h-6 w-6" /></div>
            <p className="font-medium text-white">Créer un bot Discord</p>
            <p className="mt-1 text-sm text-neutral-500">Personnalisez vos commandes</p>
          </Link>
          <Link
            href="/dashboard/minecraft/new"
            className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 text-center transition-colors hover:border-emerald-500/30 hover:bg-neutral-800"
          >
            <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400"><Server className="h-6 w-6" /></div>
            <p className="font-medium text-white">Créer un serveur Minecraft</p>
            <p className="mt-1 text-sm text-neutral-500">Toutes versions supportées</p>
          </Link>
          <Link
            href="/dashboard/sites/new"
            className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 text-center transition-colors hover:border-sky-500/30 hover:bg-neutral-800"
          >
            <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-sky-500/10 text-sky-400"><Globe className="h-6 w-6" /></div>
            <p className="font-medium text-white">Demander un site web</p>
            <p className="mt-1 text-sm text-neutral-500">Vitrine, portfolio, e-commerce</p>
          </Link>
          <Link
            href="/dashboard/apps/new"
            className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 text-center transition-colors hover:border-violet-500/30 hover:bg-neutral-800"
          >
            <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-violet-500/10 text-violet-400"><Smartphone className="h-6 w-6" /></div>
            <p className="font-medium text-white">Demander une application</p>
            <p className="mt-1 text-sm text-neutral-500">App web ou bot sur mesure</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
