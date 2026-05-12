"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { hasDevAccess } from "@/lib/roles";

interface Ticket {
  id: string;
  title: string;
  status: string;
  priority: string;
  category: string;
  createdAt: string;
  updatedAt: string;
  messages: any[];
}

const statusColors: Record<string, string> = {
  OPEN: "bg-green-500/20 text-green-400 border-green-500/30",
  PENDING: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  RESOLVED: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  CLOSED: "bg-neutral-500/20 text-neutral-400 border-neutral-500/30",
};

const priorityLabels: Record<string, string> = {
  LOW: "Basse",
  MEDIUM: "Moyenne",
  HIGH: "Haute",
  CRITICAL: "Critique",
};

export default function TicketsPage() {
  const { data: session } = useSession();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const isStaff = hasDevAccess((session?.user as any)?.roles ?? []);

  useEffect(() => {
    fetch("/api/tickets")
      .then((r) => r.json())
      .then((data) => {
        setTickets(Array.isArray(data) ? data : []);
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
        <h1 className="text-2xl font-bold text-white">Support / Tickets</h1>
        <Link
          href="/dashboard/tickets/new"
          className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
        >
          + Nouveau ticket
        </Link>
      </div>

      {isStaff && (
        <p className="text-sm text-yellow-400 mb-4">
          Mode staff — tu vois tous les tickets
        </p>
      )}

      {tickets.length === 0 ? (
        <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-8 text-center">
          <p className="text-neutral-400">Aucun ticket pour le moment.</p>
          <Link
            href="/dashboard/tickets/new"
            className="mt-4 inline-block rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
          >
            Créer un ticket
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {tickets.map((t) => (
            <Link
              key={t.id}
              href={`/dashboard/tickets/${t.id}`}
              className="flex items-center justify-between rounded-xl border border-neutral-800 bg-neutral-900 p-4 hover:border-neutral-700 transition-colors"
            >
              <div className="flex flex-col gap-1">
                <span className="font-medium text-white">{t.title}</span>
                <span className="text-xs text-neutral-500">
                  {t.category} · {priorityLabels[t.priority] ?? t.priority}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-neutral-500">
                  {t.messages.length} message{t.messages.length > 1 ? "s" : ""}
                </span>
                <span
                  className={`rounded-lg border px-2 py-0.5 text-xs font-medium ${statusColors[t.status] ?? statusColors.CLOSED}`}
                >
                  {t.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
