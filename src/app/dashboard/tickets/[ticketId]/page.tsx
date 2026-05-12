"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { hasDevAccess } from "@/lib/roles";

interface TicketMessage {
  id: string;
  authorName: string;
  content: string;
  isStaff: boolean;
  createdAt: string;
}

interface Ticket {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  category: string;
  messages: TicketMessage[];
  assignedTo: string | null;
}

const statusOptions = ["OPEN", "PENDING", "RESOLVED", "CLOSED"];

export default function TicketDetailPage() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const router = useRouter();
  const { data: session } = useSession();
  const isStaff = hasDevAccess((session?.user as any)?.roles ?? []);

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    fetch(`/api/tickets/${ticketId}`)
      .then((r) => r.json())
      .then((data) => {
        setTicket(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [ticketId]);

  async function sendReply() {
    if (!reply.trim()) return;
    setSending(true);
    try {
      const res = await fetch(`/api/tickets/${ticketId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: reply }),
      });
      if (res.ok) {
        const msg = await res.json();
        setTicket((prev) =>
          prev ? { ...prev, messages: [...prev.messages, msg] } : prev
        );
        setReply("");
      }
    } finally {
      setSending(false);
    }
  }

  async function updateStatus(status: string) {
    await fetch(`/api/tickets/${ticketId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    setTicket((prev) => (prev ? { ...prev, status } : prev));
  }

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-neutral-400">Chargement...</p>
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="p-8">
        <p className="text-red-400">Ticket introuvable.</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl">
      <button
        onClick={() => router.push("/dashboard/tickets")}
        className="mb-4 text-sm text-neutral-400 hover:text-white transition-colors"
      >
        ← Retour aux tickets
      </button>

      <div className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">{ticket.title}</h1>
            <p className="text-sm text-neutral-400 mt-1">
              {ticket.category} · Priorité {ticket.priority}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isStaff && (
              <select
                value={ticket.status}
                onChange={(e) => updateStatus(e.target.value)}
                className="rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-1.5 text-xs text-white focus:outline-none"
              >
                {statusOptions.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            )}
            {!isStaff && (
              <span className="rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-1.5 text-xs text-white">
                {ticket.status}
              </span>
            )}
          </div>
        </div>
        <p className="mt-4 text-sm text-neutral-300 whitespace-pre-wrap">{ticket.description}</p>
      </div>

      {/* Messages */}
      <div className="space-y-4 mb-6">
        {ticket.messages.map((msg) => (
          <div
            key={msg.id}
            className={`rounded-xl border p-4 ${
              msg.isStaff
                ? "border-indigo-500/20 bg-indigo-500/5"
                : "border-neutral-800 bg-neutral-900"
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium text-white">{msg.authorName}</span>
              {msg.isStaff && (
                <span className="rounded-full bg-indigo-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
                  STAFF
                </span>
              )}
              <span className="text-xs text-neutral-500">
                {new Date(msg.createdAt).toLocaleString()}
              </span>
            </div>
            <p className="text-sm text-neutral-300 whitespace-pre-wrap">{msg.content}</p>
          </div>
        ))}
      </div>

      {/* Reply */}
      {ticket.status !== "CLOSED" && (
        <div className="flex gap-3">
          <textarea
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            placeholder="Écrire une réponse..."
            rows={3}
            className="flex-1 rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white placeholder-neutral-600 focus:border-indigo-500 focus:outline-none"
          />
          <button
            onClick={sendReply}
            disabled={sending || !reply.trim()}
            className="self-end rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
          >
            {sending ? "Envoi..." : "Répondre"}
          </button>
        </div>
      )}
    </div>
  );
}
