import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import { hasRole } from "@/lib/roles";

export async function GET() {
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { discordId: session.user.discordId },
  });

  if (!user || !hasRole(user.roles, "MANAGER")) {
    return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
  }

  const users = await prisma.user.findMany({
    orderBy: { createdAt: "desc" },
    include: {
      _count: {
        select: { bots: true, minecraftServers: true, sites: true, apps: true },
      },
      subscription: true,
    },
  });

  return NextResponse.json(
    users.map((u) => ({
      id: u.id,
      discordId: u.discordId,
      username: u.username,
      avatar: u.avatar,
      roles: u.roles,
      kronesBalance: u.kronesBalance,
      kronesSpent: u.kronesSpent,
      subscription: u.subscription,
      boxQuotaMb: u.boxQuotaMb,
      totalServices:
        u._count.bots + u._count.minecraftServers + u._count.sites + u._count.apps,
      createdAt: u.createdAt,
    }))
  );
}
