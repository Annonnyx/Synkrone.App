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

  const bots = await prisma.bot.findMany({
    orderBy: { createdAt: "desc" },
    include: { user: { select: { username: true } } },
  });

  return NextResponse.json(
    bots.map((b) => ({
      id: b.id,
      botName: b.botName,
      ownerName: b.user?.username ?? "Inconnu",
      prefix: b.prefix,
      cogs: b.cogs,
      status: b.status,
      kronesConsumed: b.kronesConsumed,
      groupId: b.groupId,
      createdAt: b.createdAt,
    }))
  );
}
