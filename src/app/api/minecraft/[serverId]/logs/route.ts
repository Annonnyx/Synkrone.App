import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import fs from "fs/promises";

export async function GET(_: Request, { params }: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });

  const user = await prisma.user.findUnique({ where: { discordId: session.user.discordId } });
  if (!user) return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });

  const server = await prisma.minecraftServer.findUnique({ where: { id: serverId } });
  if (!server || server.userId !== user.id) return NextResponse.json({ error: "Serveur introuvable" }, { status: 404 });

  const logPath = `/root/.pm2/logs/mc_${server.id}-out.log`;

  try {
    const content = await fs.readFile(logPath, "utf-8");
    const lines = content.split("\n").slice(-200).join("\n");
    return NextResponse.json({ logs: lines });
  } catch {
    return NextResponse.json({ logs: "Aucun log disponible." });
  }
}
