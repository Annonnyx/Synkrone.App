"use client";

import { LucideIcon } from "lucide-react";

interface StepItemProps {
  step: number;
  icon: LucideIcon;
  title: string;
  description: string;
}

export function StepItem({ step, icon: Icon, title, description }: StepItemProps) {
  return (
    <div className="relative flex flex-col items-center text-center">
      <div className="relative mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 text-indigo-300 ring-1 ring-white/10">
        <Icon className="h-6 w-6" />
        <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-[10px] font-bold text-white">
          {step}
        </span>
      </div>
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <p className="mt-2 max-w-xs text-sm leading-relaxed text-neutral-400">{description}</p>
    </div>
  );
}
