"use client";

import { useState, useMemo } from "react";
import { Bot, Server, Globe, Smartphone, Zap, ArrowRight, Minus, Plus, Check } from "lucide-react";

type Period = "monthly" | "yearly";

interface Config {
  bots: number;
  minecraftRam: number; // in GB
  sites: number;
  apps: number;
  credits: number; // in hundreds
}

const PRICES = {
  bot: 5.99,
  minecraftPerGb: 7.99,
  site: 9.99,
  app: 12.99,
  creditsPer100: 1.99,
};

function Stepper({
  value,
  onChange,
  min = 0,
  max = 10,
}: {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
}) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onChange(Math.max(min, value - 1))}
        className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] text-neutral-300 transition-colors hover:bg-white/[0.06] hover:text-white disabled:opacity-30"
        disabled={value <= min}
      >
        <Minus className="h-3.5 w-3.5" />
      </button>
      <span className="w-8 text-center font-semibold text-white tabular-nums">{value}</span>
      <button
        onClick={() => onChange(Math.min(max, value + 1))}
        className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] text-neutral-300 transition-colors hover:bg-white/[0.06] hover:text-white disabled:opacity-30"
        disabled={value >= max}
      >
        <Plus className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

function LineItem({
  icon: Icon,
  label,
  qty,
  unitPrice,
  total,
}: {
  icon: React.ElementType;
  label: string;
  qty: number;
  unitPrice: number;
  total: number;
}) {
  if (qty <= 0) return null;
  return (
    <div className="flex items-center justify-between py-2 text-sm">
      <div className="flex items-center gap-2 text-neutral-300">
        <Icon className="h-4 w-4 text-cyan-accent opacity-80" />
        <span>
          {qty} × {label}
        </span>
      </div>
      <span className="font-medium text-white">{total.toFixed(2)} €</span>
    </div>
  );
}

export default function PricingBuilder() {
  const [period, setPeriod] = useState<Period>("monthly");
  const [cfg, setCfg] = useState<Config>({
    bots: 1,
    minecraftRam: 2,
    sites: 0,
    apps: 0,
    credits: 5,
  });

  const monthlyRaw = useMemo(() => {
    return (
      cfg.bots * PRICES.bot +
      cfg.minecraftRam * PRICES.minecraftPerGb +
      cfg.sites * PRICES.site +
      cfg.apps * PRICES.app +
      cfg.credits * PRICES.creditsPer100
    );
  }, [cfg]);

  const serviceCount = cfg.bots + (cfg.minecraftRam > 0 ? 1 : 0) + cfg.sites + cfg.apps;

  const volumeDiscount = useMemo(() => {
    if (serviceCount >= 6) return 0.25;
    if (serviceCount >= 4) return 0.15;
    if (serviceCount >= 2) return 0.1;
    return 0;
  }, [serviceCount]);

  const periodDiscount = period === "yearly" ? 0.2 : 0;

  const afterVolume = monthlyRaw * (1 - volumeDiscount);
  const afterPeriod = afterVolume * (1 - periodDiscount);

  const monthlyPrice = afterPeriod;
  const yearlyPrice = monthlyPrice * 12;

  const discountLabel =
    volumeDiscount > 0 && periodDiscount > 0
      ? `-${Math.round((volumeDiscount + periodDiscount - volumeDiscount * periodDiscount) * 100)}%`
      : volumeDiscount > 0
        ? `-${Math.round(volumeDiscount * 100)}%`
        : periodDiscount > 0
          ? "-20%"
          : null;

  return (
    <div className="mx-auto max-w-5xl">
      {/* Period toggle */}
      <div className="mb-10 flex justify-center">
        <div className="inline-flex items-center gap-1 rounded-xl border border-white/10 bg-white/[0.03] p-1">
          <button
            onClick={() => setPeriod("monthly")}
            className={`rounded-lg px-5 py-2 text-sm font-medium transition-all ${
              period === "monthly"
                ? "bg-gradient-to-r from-[#00e1ff] to-[#5865F2] text-white shadow-lg shadow-cyan-500/20"
                : "text-neutral-400 hover:text-neutral-200"
            }`}
          >
            Mensuel
          </button>
          <button
            onClick={() => setPeriod("yearly")}
            className={`rounded-lg px-5 py-2 text-sm font-medium transition-all ${
              period === "yearly"
                ? "bg-gradient-to-r from-[#00e1ff] to-[#5865F2] text-white shadow-lg shadow-cyan-500/20"
                : "text-neutral-400 hover:text-neutral-200"
            }`}
          >
            Annuel <span className="text-xs opacity-80">-20%</span>
          </button>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Configurator */}
        <div className="space-y-5">
          {[
            {
              key: "bots" as const,
              icon: Bot,
              label: "Bots Discord",
              subtitle: `${PRICES.bot.toFixed(2)} €/mois chacun`,
              value: cfg.bots,
              max: 20,
            },
            {
              key: "minecraftRam" as const,
              icon: Server,
              label: "Serveur Minecraft",
              subtitle: `${PRICES.minecraftPerGb.toFixed(2)} €/mois par Go RAM`,
              value: cfg.minecraftRam,
              max: 16,
            },
            {
              key: "sites" as const,
              icon: Globe,
              label: "Sites Web",
              subtitle: `${PRICES.site.toFixed(2)} €/mois chacun`,
              value: cfg.sites,
              max: 10,
            },
            {
              key: "apps" as const,
              icon: Smartphone,
              label: "Applications",
              subtitle: `${PRICES.app.toFixed(2)} €/mois chacune`,
              value: cfg.apps,
              max: 10,
            },
            {
              key: "credits" as const,
              icon: Zap,
              label: "Crédits Krônes",
              subtitle: `${PRICES.creditsPer100.toFixed(2)} € pour 100 Kr/mois`,
              value: cfg.credits,
              max: 50,
            },
          ].map((item) => (
            <div
              key={item.key}
              className="flex items-center justify-between rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 transition-colors hover:border-white/[0.1]"
            >
              <div className="flex items-center gap-4">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-accent ring-1 ring-white/10">
                  <item.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-semibold text-white">{item.label}</p>
                  <p className="text-xs text-neutral-500">{item.subtitle}</p>
                </div>
              </div>
              <Stepper
                value={item.value}
                onChange={(v) => setCfg((prev) => ({ ...prev, [item.key]: v }))}
                max={item.max}
              />
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="sticky top-6 h-fit">
          <div className="rounded-2xl border border-white/[0.08] bg-gradient-to-b from-white/[0.05] to-white/[0.02] p-6 backdrop-blur-sm">
            <h3 className="text-lg font-bold text-white">Récapitulatif</h3>
            <p className="text-xs text-neutral-500">
              {serviceCount} service{serviceCount > 1 ? "s" : ""} sélectionné
              {serviceCount > 1 ? "s" : ""}
            </p>

            <div className="mt-4 space-y-1">
              <LineItem
                icon={Bot}
                label="Bot Discord"
                qty={cfg.bots}
                unitPrice={PRICES.bot}
                total={cfg.bots * PRICES.bot}
              />
              <LineItem
                icon={Server}
                label={`Go RAM MC`}
                qty={cfg.minecraftRam}
                unitPrice={PRICES.minecraftPerGb}
                total={cfg.minecraftRam * PRICES.minecraftPerGb}
              />
              <LineItem
                icon={Globe}
                label="Site Web"
                qty={cfg.sites}
                unitPrice={PRICES.site}
                total={cfg.sites * PRICES.site}
              />
              <LineItem
                icon={Smartphone}
                label="Application"
                qty={cfg.apps}
                unitPrice={PRICES.app}
                total={cfg.apps * PRICES.app}
              />
              <LineItem
                icon={Zap}
                label="× 100 Krônes"
                qty={cfg.credits}
                unitPrice={PRICES.creditsPer100}
                total={cfg.credits * PRICES.creditsPer100}
              />
            </div>

            {volumeDiscount > 0 && (
              <div className="mt-3 flex items-center justify-between rounded-lg bg-emerald-500/10 px-3 py-2 text-sm text-emerald-400">
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5" />
                  Réduction volume ({serviceCount} services)
                </span>
                <span>-{Math.round(volumeDiscount * 100)}%</span>
              </div>
            )}

            {period === "yearly" && (
              <div className="mt-2 flex items-center justify-between rounded-lg bg-cyan-500/10 px-3 py-2 text-sm text-cyan-accent">
                <span className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5" />
                  Engagement annuel
                </span>
                <span>-20%</span>
              </div>
            )}

            <div className="my-5 border-t border-white/[0.08]" />

            <div className="flex items-end justify-between">
              <div>
                <p className="text-xs text-neutral-500">
                  {period === "yearly" ? "Paiement annuel" : "Par mois"}
                </p>
                <p className="text-3xl font-extrabold text-white">
                  {period === "yearly"
                    ? `${yearlyPrice.toFixed(2)} €`
                    : `${monthlyPrice.toFixed(2)} €`}
                  <span className="text-sm font-medium text-neutral-500">
                    {period === "yearly" ? "/an" : "/mois"}
                  </span>
                </p>
              </div>
              {discountLabel && (
                <span className="rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-bold text-emerald-400">
                  {discountLabel}
                </span>
              )}
            </div>

            <button className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#00e1ff] to-[#5865F2] px-6 py-3 text-sm font-bold text-[#0a0a0a] shadow-lg shadow-cyan-500/20 transition-all hover:brightness-110 active:scale-[0.98]">
              Souscrire <ArrowRight className="h-4 w-4" />
            </button>

            <p className="mt-3 text-center text-xs text-neutral-500">
              Sans engagement. Modifiez votre configuration à tout moment.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
