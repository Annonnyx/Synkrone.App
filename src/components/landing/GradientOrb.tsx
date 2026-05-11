"use client";

export function GradientOrb({
  className = "",
  delay = 0,
}: {
  className?: string;
  delay?: number;
}) {
  return (
    <div
      className={`absolute rounded-full blur-3xl opacity-20 animate-pulse-glow pointer-events-none ${className}`}
      style={{ animationDelay: `${delay}s` }}
    />
  );
}
