export const STATUS_COLORS = {
  ONLINE:   { bg: "bg-emerald-500/10", text: "text-emerald-400", dot: "bg-emerald-500" },
  OFFLINE:  { bg: "bg-neutral-500/10", text: "text-neutral-400", dot: "bg-neutral-500" },
  ERROR:    { bg: "bg-red-500/10",     text: "text-red-400",     dot: "bg-red-500"     },
  PAUSED:   { bg: "bg-amber-500/10",   text: "text-amber-400",   dot: "bg-amber-500"   },
  PENDING:  { bg: "bg-blue-500/10",    text: "text-blue-400",    dot: "bg-blue-500"    },
  IN_PROGRESS: { bg: "bg-indigo-500/10", text: "text-indigo-400", dot: "bg-indigo-500" },
  REVIEW:   { bg: "bg-purple-500/10",  text: "text-purple-400",  dot: "bg-purple-500"  },
} as const;

export const ROLE_COLORS: Record<string, string> = {
  USER:       "bg-neutral-700 text-neutral-300",
  SUPPORT:    "bg-blue-900/50 text-blue-300",
  DEV_TEST:   "bg-teal-900/50 text-teal-300",
  DEV_DEV:    "bg-cyan-900/50 text-cyan-300",
  DEV_ELITE:  "bg-sky-900/50 text-sky-300",
  MANAGER:    "bg-violet-900/50 text-violet-300",
  SUPERVISOR: "bg-purple-900/50 text-purple-300",
  LEADER:     "bg-amber-900/50 text-amber-300",
};
