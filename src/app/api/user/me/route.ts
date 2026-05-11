import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

export async function GET() {
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { discordId: session.user.discordId },
    include: { subscription: true },
  });

  if (!user) {
    return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });
  }

  return NextResponse.json({
    id: user.id,
    discordId: user.discordId,
    username: user.username,
    avatar: user.avatar,
    roles: user.roles,
    kronesBalance: user.kronesBalance,
    kronesSpent: user.kronesSpent,
    subscription: user.subscription,
    boxQuotaMb: user.boxQuotaMb,
    boxUsedMb: 0,
    createdAt: user.createdAt,
  });
}
