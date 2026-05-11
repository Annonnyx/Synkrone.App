import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import { hasRole } from "@/lib/roles";

export async function PATCH(req: Request, { params }: { params: Promise<{ userId: string }> }) {
  const { userId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const actor = await prisma.user.findUnique({
    where: { discordId: session.user.discordId },
  });

  if (!actor || !hasRole(actor.roles, "MANAGER")) {
    return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
  }

  const { amount, reason } = await req.json();

  if (!amount || !reason) {
    return NextResponse.json({ error: "Paramètres manquants" }, { status: 400 });
  }

  const targetUser = await prisma.user.findUnique({
    where: { id: userId },
  });

  if (!targetUser) {
    return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });
  }

  // Si c'est un débit, vérifier le solde
  if (amount < 0 && targetUser.kronesBalance + amount < 0) {
    return NextResponse.json({ error: "Solde insuffisant pour ce débit" }, { status: 402 });
  }

  await prisma.$transaction([
    prisma.user.update({
      where: { id: userId },
      data: {
        kronesBalance: { increment: amount },
        ...(amount < 0 ? { kronesSpent: { increment: -amount } } : {}),
      },
    }),
    prisma.kroneTransaction.create({
      data: {
        userId,
        amount,
        reason: `ADMIN_${amount >= 0 ? "GRANT" : "DEDUCT"}: ${reason}`,
        relatedId: actor.id,
      },
    }),
    prisma.adminLog.create({
      data: {
        actorId: actor.id,
        action: amount >= 0 ? "GRANT_KRONES" : "DEDUCT_KRONES",
        target: userId,
        details: `${amount} Kr — Raison: ${reason}`,
      },
    }),
  ]);

  return NextResponse.json({ success: true });
}
