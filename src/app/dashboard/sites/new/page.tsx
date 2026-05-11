"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const siteTypes = ["Vitrine", "Portfolio", "E-commerce", "Blog", "Application web", "Autre"];
const technologies = ["HTML/CSS/JS", "React", "Next.js", "WordPress", "Autre"];
const budgets = ["< 100€", "100€ - 500€", "500€ - 1000€", "1000€ - 5000€", "Sur devis"];

export default function NewSitePage() {
  const router = useRouter();
  const [projectName, setProjectName] = useState("");
  const [description, setDescription] = useState("");
  const [siteType, setSiteType] = useState("Vitrine");
  const [tech, setTech] = useState("");
  const [budget, setBudget] = useState("< 100€");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const descLen = description.length;
  const isValid = projectName.trim().length > 0 && descLen >= 50;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid) return;
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/sites/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          projectName: projectName.trim(),
          description: description.trim(),
          siteType,
          technology: tech || undefined,
          budget,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Une erreur est survenue");
      } else {
        setSuccess(true);
      }
    } catch {
      setError("Erreur réseau. Réessayez.");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="p-8 max-w-xl">
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-8 text-center">
          <div className="text-4xl mb-3">🎉</div>
          <h2 className="text-xl font-bold text-white mb-2">Demande envoyée !</h2>
          <p className="text-emerald-300 text-sm mb-6">Notre équipe vous contactera sous 48h.</p>
          <Link
            href="/dashboard"
            className="inline-block rounded-xl bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-500"
          >
            Retour au dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-2">Demander un site web</h1>
      <p className="text-neutral-400 text-sm mb-8">Décrivez votre projet et notre équipe vous recontactera.</p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1.5">Nom du projet *</label>
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="MaBoutiqueEnLigne"
            className="w-full rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white placeholder-neutral-600 focus:border-indigo-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1.5">
            Description du site souhaité * <span className="text-neutral-500">(min. 50 caractères)</span>
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={5}
            placeholder="Je souhaite un site vitrine pour présenter mon activité de photographe..."
            className="w-full rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white placeholder-neutral-600 focus:border-indigo-500 focus:outline-none resize-none"
          />
          <p className={`mt-1 text-xs ${descLen < 50 ? "text-red-400" : "text-neutral-500"}`}>
            {descLen}/50 caractères
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1.5">Type de site *</label>
          <select
            value={siteType}
            onChange={(e) => setSiteType(e.target.value)}
            className="w-full rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none appearance-none"
          >
            {siteTypes.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1.5">Technologies préférées (optionnel)</label>
          <select
            value={tech}
            onChange={(e) => setTech(e.target.value)}
            className="w-full rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none appearance-none"
          >
            <option value="">Non spécifié</option>
            {technologies.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-300 mb-1.5">Budget estimé *</label>
          <select
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            className="w-full rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none appearance-none"
          >
            {budgets.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-3 pt-2">
          <a
            href="https://discord.gg/synkrone"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-4 py-2 text-sm font-medium text-indigo-300 transition-colors hover:bg-indigo-500/20"
          >
            Prendre rendez-vous sur Discord
          </a>
          <a
            href="mailto:contact@synkrone.app"
            className="rounded-lg border border-neutral-800 bg-neutral-900 px-4 py-2 text-sm font-medium text-neutral-300 transition-colors hover:bg-neutral-800"
          >
            Nous contacter par email
          </a>
        </div>

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-5 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        <div className="pt-2">
          <button
            type="submit"
            disabled={!isValid || loading}
            className="rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? "Envoi en cours..." : "Envoyer la demande"}
          </button>
        </div>
      </form>
    </div>
  );
}
