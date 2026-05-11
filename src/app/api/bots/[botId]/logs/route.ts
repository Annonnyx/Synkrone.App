import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import fs from "fs/promises";

export async function GET(_: Request, { params }: { params: Promise<{ botId: string }> }) {
  const { botId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });

  const user = await prisma.user.findUnique({ where: { discordId: session.user.discordId } });
  if (!user) return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });

  const bot = await prisma.bot.findUnique({ where: { id: botId } });
  if (!bot || bot.userId !== user.id) return NextResponse.json({ error: "Bot introuvable" }, { status: 404 });

  const logPath = `/var/log/synkrone/synkrone_${bot.id}.out.log`;

  try {
    const content = await fs.readFile(logPath, "utf-8");
    // Retourner les 200 dernières lignes
    const lines = content.split("\n").slice(-200).join("\n");
    return NextResponse.json({ logs: lines });
  } catch {
    return NextResponse.json({ logs: "Aucun log disponible." });
  }
}
