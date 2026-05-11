"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { KrBadge } from "@/components/ui/KrBadge";

const purchaseOffers = [
  { id: "starter", name: "Starter", kr: 500, price: "2,99€" },
  { id: "basic", name: "Basic", kr: 1200, price: "5,99€" },
  { id: "pro", name: "Pro", kr: 2500, price: "9,99€" },
  { id: "studio", name: "Studio", kr: 6000, price: "19,99€" },
  { id: "enterprise", name: "Enterprise", kr: 15000, price: "39,99€" },
];

const subscriptions = [
  { name: "Starter", price: "4,99€/mois", kr: 800 },
  { name: "Pro", price: "9,99€/mois", kr: 2000 },
  { name: "Studio", price: "19,99€/mois", kr: 5000 },
  { name: "Enterprise", price: "Sur devis", kr: 0 },
];

const reasonLabels: Record<string, string> = {
  BOT_CREATION: "Création de bot",
  MC_CREATION: "Création serveur Minecraft",
  SITE_REQUEST: "Demande de site web",
  APP_REQUEST: "Demande d'application",
  SUBSCRIPTION: "Abonnement",
  REFUND: "Remboursement",
  PURCHASE: "Achat de Krônes",
  ADMIN_GRANT: "Ajout par un administrateur",
  ADMIN_DEDUCT: "Retrait par un administrateur",
};

interface Transaction {
  id: string;
  amount: number;
  reason: string;
  relatedId: string | null;
  createdAt: string;
}

function CoinIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
}

export default function KronesPage() {
  const { data: session } = useSession();
  const [balance, setBalance] = useState(0);
  const [spent, setSpent] = useState(0);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [txLoading, setTxLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState("");

  useEffect(() => {
    fetch("/api/krones/balance")
      .then((r) => r.json())
      .then((data) => {
        setBalance(data.balance ?? 0);
        setSpent(data.spent ?? 0);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetch("/api/krones/transactions")
      .then((r) => r.json())
      .then((data: Transaction[]) => {
        setTransactions(data);
        setTxLoading(false);
      })
      .catch(() => setTxLoading(false));
  }, []);

  function openModal(title: string) {
    setModalTitle(title);
    setModalOpen(true);
  }

  if (loading) {
    return (
      <div className="p-8">
        <p className="text-neutral-400">Chargement...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl space-y-10">
      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl border border-neutral-800 bg-neutral-900 p-6 shadow-2xl text-center">
            <h3 className="text-lg font-bold text-white mb-2">{modalTitle}</h3>
            <p className="text-sm text-neutral-400 mb-6">
              Paiement en cours de développement — Contactez-nous sur Discord pour l'instant.
            </p>
            <div className="flex gap-3 justify-center">
              <a
                href="https://discord.gg/synkrone"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-xl bg-indigo-600 px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
              >
                Discord
              </a>
              <button
                onClick={() => setModalOpen(false)}
                className="rounded-xl border border-neutral-800 bg-neutral-900 px-5 py-2 text-sm font-medium text-neutral-300 hover:bg-neutral-800 transition-colors"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Carte solde */}
      <div className="rounded-2xl border border-yellow-500/20 bg-yellow-500/5 p-8">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-yellow-500/10">
            <CoinIcon className="h-7 w-7 text-yellow-400" />
          </div>
          <div>
            <p className="text-sm text-neutral-400">Mon solde</p>
            <p className="text-3xl font-extrabold"><KrBadge amount={balance} /></p>
            <p className="mt-1 text-sm text-neutral-500">
              <KrBadge amount={spent} /> dépensés au total
            </p>
          </div>
        </div>
      </div>

      {/* Acheter des Krônes */}
      <section>
        <h2 className="text-xl font-bold text-white mb-4">Acheter des Krônes</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {purchaseOffers.map((offer) => (
            <div key={offer.id} className="rounded-xl border border-neutral-800 bg-neutral-900 p-5 flex flex-col items-center text-center gap-3">
              <h3 className="font-semibold text-white">{offer.name}</h3>
              <div className="text-2xl font-extrabold"><KrBadge amount={offer.kr} /></div>
              <p className="text-sm text-neutral-400">{offer.price}</p>
              <button
                onClick={() => openModal(`Acheter ${offer.name}`)}
                className="mt-auto w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-indigo-500"
              >
                Acheter
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Abonnements */}
      <section>
        <h2 className="text-xl font-bold text-white mb-4">Abonnements</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {subscriptions.map((sub) => (
            <div
              key={sub.name}
              className={`rounded-xl border p-5 flex flex-col items-center text-center gap-3 ${
                sub.name === "Pro" ? "border-indigo-500/30 bg-neutral-900 ring-1 ring-indigo-500/20" : "border-neutral-800 bg-neutral-900"
              }`}
            >
              <h3 className="font-semibold text-white">{sub.name}</h3>
              <p className="text-2xl font-extrabold text-white">{sub.price}</p>
              {sub.kr > 0 && (
                <p className="text-sm text-neutral-400"><KrBadge amount={sub.kr} />/mois</p>
              )}
              <button
                onClick={() => openModal(`S'abonner ${sub.name}`)}
                className="mt-auto w-full rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2 text-sm font-medium text-neutral-300 transition-colors hover:border-indigo-500/30 hover:text-white"
              >
                S'abonner
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Historique */}
      <section>
        <h2 className="text-xl font-bold text-white mb-4">Historique des transactions</h2>
        {txLoading ? (
          <p className="text-neutral-400 text-sm">Chargement...</p>
        ) : transactions.length === 0 ? (
          <p className="text-neutral-500 text-sm">Aucune transaction.</p>
        ) : (
          <div className="rounded-xl border border-neutral-800 bg-neutral-900 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-800 bg-neutral-900/80 text-left">
                  <th className="px-5 py-3 font-medium text-neutral-400">Date</th>
                  <th className="px-5 py-3 font-medium text-neutral-400">Raison</th>
                  <th className="px-5 py-3 font-medium text-neutral-400 text-right">Montant</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.id} className="border-b border-neutral-800/50">
                    <td className="px-5 py-3 text-neutral-300 whitespace-nowrap">
                      {new Date(tx.createdAt).toLocaleDateString("fr-FR", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="px-5 py-3 text-white">{reasonLabels[tx.reason] ?? tx.reason}</td>
                    <td className="px-5 py-3 text-right">
                      <KrBadge amount={tx.amount} showSign />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
