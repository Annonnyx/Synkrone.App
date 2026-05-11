"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Package, FolderOpen } from "lucide-react";

export default function BoxesPage() {
  const { data: session } = useSession();
  const userId = session?.user?.dbId;

  if (!userId) {
    return (
      <div className="p-8">
        <p className="text-neutral-400">Chargement...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-white">Boxes</h1>
      <p className="text-neutral-400 text-sm">
        Sélectionnez votre box personnelle ou la box partagée avec l'équipe.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          href={`/dev/boxes/${userId}`}
          className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 transition-colors hover:border-cyan-500/30 hover:bg-neutral-800"
        >
          <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400"><Package className="h-6 w-6" /></div>
          <h3 className="font-semibold text-white">Ma Box</h3>
          <p className="mt-1 text-sm text-neutral-500">Vos fichiers personnels et projets</p>
        </Link>

        <Link
          href="/dev/boxes/shared"
          className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 transition-colors hover:border-cyan-500/30 hover:bg-neutral-800"
        >
          <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400"><FolderOpen className="h-6 w-6" /></div>
          <h3 className="font-semibold text-white">Box Partagée</h3>
          <p className="mt-1 text-sm text-neutral-500">Fichiers partagés avec l'équipe</p>
        </Link>
      </div>
    </div>
  );
}
