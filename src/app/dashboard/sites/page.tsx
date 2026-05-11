"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { StatusBadge } from "@/components/ui/StatusBadge";

type Site = {
  id: string;
  projectName: string;
  description: string;
  siteType: string;
  status: string;
  url: string | null;
};

export default function SitesPage() {
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/user/services")
      .then((r) => r.json())
      .then((data) => {
        setSites(data.sites ?? []);
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
        <h1 className="text-2xl font-bold text-white">Mes Sites Web</h1>
        <Link
          href="/dashboard/sites/new"
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
        >
          + Demander un site web
        </Link>
      </div>

      {sites.length === 0 ? (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-8 text-center">
          <p className="text-neutral-400">Vous n'avez pas encore de sites web.</p>
          <Link
            href="/dashboard/sites/new"
            className="mt-4 inline-block rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
          >
            Demander mon premier site
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sites.map((site) => (
            <div key={site.id} className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white truncate">{site.projectName}</h3>
                <StatusBadge status={site.status as any} />
              </div>
              <p className="text-sm text-neutral-400 truncate">{site.description}</p>
              <div className="flex items-center justify-between mt-auto">
                <span className="text-xs text-neutral-500">{site.siteType}</span>
                {site.url ? (
                  <a href={site.url} target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-400 hover:underline">
                    Voir le site
                  </a>
                ) : (
                  <span className="text-xs text-neutral-600">En développement</span>
                )}
              </div>
              <Link
                href={`/dashboard/sites/${site.id}`}
                className="mt-2 w-full rounded-lg bg-neutral-800 px-4 py-2 text-center text-sm font-medium text-white transition-colors hover:bg-neutral-700"
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
