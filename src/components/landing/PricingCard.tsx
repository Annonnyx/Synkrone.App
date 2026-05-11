"use client";

interface PricingCardProps {
  name: string;
  price: string;
  period?: string;
  features: string[];
  highlighted?: boolean;
  cta?: string;
  onCta?: () => void;
}

export function PricingCard({
  name,
  price,
  period = "/mois",
  features,
  highlighted = false,
  cta = "Choisir",
  onCta,
}: PricingCardProps) {
  return (
    <div
      className={`relative flex flex-col rounded-2xl border p-6 transition-all duration-300 hover:-translate-y-1 ${
        highlighted
          ? "border-indigo-500/30 bg-gradient-to-b from-indigo-500/[0.07] to-transparent ring-1 ring-indigo-500/20"
          : "border-white/[0.06] bg-white/[0.02] glow-border"
      }`}
    >
      {highlighted && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 px-3 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-white">
          Populaire
        </div>
      )}
      <h3 className="text-xl font-bold text-white">{name}</h3>
      <div className="mt-3 flex items-baseline gap-1">
        <span className="text-4xl font-extrabold text-white">{price}</span>
        <span className="text-sm text-neutral-500">{period}</span>
      </div>
      <ul className="mt-6 flex-1 space-y-3">
        {features.map((f, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-neutral-300">
            <svg className="mt-0.5 h-4 w-4 shrink-0 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            {f}
          </li>
        ))}
      </ul>
      <button
        onClick={onCta}
        className={`mt-6 w-full rounded-xl py-2.5 text-sm font-semibold transition-colors ${
          highlighted
            ? "bg-indigo-600 text-white hover:bg-indigo-500"
            : "border border-white/10 bg-white/[0.04] text-white hover:bg-white/[0.08]"
        }`}
      >
        {cta}
      </button>
    </div>
  );
}
