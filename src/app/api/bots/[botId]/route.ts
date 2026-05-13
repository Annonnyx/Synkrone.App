import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import { hasRole } from "@/lib/roles";

async function getBot(botId: string, discordId: string) {
  const user = await prisma.user.findUnique({ where: { discordId } });
  if (!user) return null;
  const bot = await prisma.bot.findUnique({
    where: { id: botId },
    include: { stats: true },
  });
  if (!bot) return null;
  // Vérifier que l'utilisateur est propriétaire OU admin
  const isOwner = bot.userId === user.id;
  const isAdmin = hasRole(user.roles, "MANAGER");
  if (!isOwner && !isAdmin) return null;
  return bot;
}

export async function GET(_: Request, { params }: { params: Promise<{ botId: string }> }) {
  const { botId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  const bot = await getBot(botId, session.user.discordId);
  if (!bot) return NextResponse.json({ error: "Bot introuvable" }, { status: 404 });
  return NextResponse.json(bot);
}

export async function PATCH(req: Request, { params }: { params: Promise<{ botId: string }> }) {
  const { botId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  const bot = await getBot(botId, session.user.discordId);
  if (!bot) return NextResponse.json({ error: "Bot introuvable" }, { status: 404 });
  const { botName, prefix } = await req.json();
  const updated = await prisma.bot.update({
    where: { id: botId },
    data: { ...(botName && { botName }), ...(prefix && { prefix }) },
  });
  return NextResponse.json(updated);
}

export async function DELETE(_: Request, { params }: { params: Promise<{ botId: string }> }) {
  const { botId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  const bot = await getBot(botId, session.user.discordId);
  if (!bot) return NextResponse.json({ error: "Bot introuvable" }, { status: 404 });
  await prisma.botStats.deleteMany({ where: { botId } });
  await prisma.bot.delete({ where: { id: botId } });
  return NextResponse.json({ success: true });
}
