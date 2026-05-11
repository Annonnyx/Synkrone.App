import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import { hasRole } from "@/lib/roles";

async function getServer(serverId: string, discordId: string) {
  const user = await prisma.user.findUnique({ where: { discordId } });
  if (!user) return null;
  const server = await prisma.minecraftServer.findUnique({
    where: { id: serverId },
    include: { backups: { orderBy: { createdAt: "desc" } } },
  });
  if (!server) return null;
  const isOwner = server.userId === user.id;
  const isAdmin = hasRole(user.roles, "MANAGER");
  if (!isOwner && !isAdmin) return null;
  return server;
}

export async function GET(_: Request, { params }: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  const server = await getServer(serverId, session.user.discordId);
  if (!server) return NextResponse.json({ error: "Serveur introuvable" }, { status: 404 });
  return NextResponse.json(server);
}

export async function PATCH(req: Request, { params }: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  const server = await getServer(serverId, session.user.discordId);
  if (!server) return NextResponse.json({ error: "Serveur introuvable" }, { status: 404 });
  const { serverName, ramMb, maxPlayers } = await req.json();
  const kronesPerMonth = ramMb ? Math.ceil(ramMb / 1024) * 50 : server.kronesPerMonth;
  const updated = await prisma.minecraftServer.update({
    where: { id: serverId },
    data: {
      ...(serverName && { serverName }),
      ...(ramMb && { ramMb, kronesPerMonth }),
      ...(maxPlayers !== undefined && { maxPlayers }),
    },
  });
  return NextResponse.json(updated);
}

export async function DELETE(_: Request, { params }: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  const server = await getServer(serverId, session.user.discordId);
  if (!server) return NextResponse.json({ error: "Serveur introuvable" }, { status: 404 });
  await prisma.minecraftServer.delete({ where: { id: serverId } });
  return NextResponse.json({ success: true });
}
