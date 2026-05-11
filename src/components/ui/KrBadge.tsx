export function KrBadge({ amount, showSign = false }: { amount: number; showSign?: boolean }) {
  const isPositive = amount >= 0;
  const color = showSign ? (isPositive ? "text-emerald-400" : "text-red-400") : "text-amber-400";
  const sign = showSign ? (isPositive ? "+" : "") : "";
  return (
    <span className={`font-mono font-semibold ${color}`}>
      {sign}{amount.toLocaleString("fr-FR")} Kr
    </span>
  );
}
