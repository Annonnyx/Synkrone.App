import { ROLE_COLORS } from "@/lib/ui/design-tokens";

export function RoleBadge({ role }: { role: string }) {
  const colorClass = ROLE_COLORS[role] ?? "bg-neutral-700 text-neutral-300";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-semibold ${colorClass}`}>
      {role}
    </span>
  );
}
