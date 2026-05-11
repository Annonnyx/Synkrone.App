import { STATUS_COLORS } from "@/lib/ui/design-tokens";

type Status = keyof typeof STATUS_COLORS;

interface StatusBadgeProps {
  status: Status;
  label?: string;
}

const STATUS_LABELS: Record<Status, string> = {
  ONLINE: "En ligne",
  OFFLINE: "Hors ligne",
  ERROR: "Erreur",
  PAUSED: "En pause",
  PENDING: "En attente",
  IN_PROGRESS: "En développement",
  REVIEW: "En révision",
};

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const colors = STATUS_COLORS[status] ?? STATUS_COLORS.OFFLINE;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${colors.dot}`} />
      {label ?? STATUS_LABELS[status] ?? status}
    </span>
  );
}
