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
    include: {
      bots: { include: { stats: true } },
      minecraftServers: true,
      sites: true,
      apps: true,
    },
  });

  if (!user) {
    return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });
  }

  const services = [
    ...user.bots.map((b) => ({ id: b.id, name: b.botName, type: "bot" as const, status: b.status })),
    ...user.minecraftServers.map((s) => ({ id: s.id, name: s.serverName, type: "minecraft" as const, status: s.status })),
    ...user.sites.map((s) => ({ id: s.id, name: s.projectName, type: "site" as const, status: s.status })),
    ...user.apps.map((a) => ({ id: a.id, name: a.appName, type: "app" as const, status: a.status })),
  ];

  return NextResponse.json(services);
}
