import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export async function POST(req: Request, { params }: { params: Promise<{ botId: string }> }) {
  const { botId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });

  const { action } = await req.json(); // "start" | "stop" | "restart"
  const validActions = ["start", "stop", "restart"];
  if (!validActions.includes(action)) {
    return NextResponse.json({ error: "Action invalide" }, { status: 400 });
  }

  const user = await prisma.user.findUnique({ where: { discordId: session.user.discordId } });
  if (!user) return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });

  const bot = await prisma.bot.findUnique({ where: { id: botId } });
  if (!bot || bot.userId !== user.id) return NextResponse.json({ error: "Bot introuvable" }, { status: 404 });

  const containerName = bot.groupId ? `synkrone-bots-group-${bot.groupId}` : null;

  try {
    // En environnement de production, exécuter la commande Docker supervisorctl
    if (containerName) {
      const supervisorAction = action === "start" ? "start" : action === "stop" ? "stop" : "restart";
      await execAsync(`docker exec ${containerName} supervisorctl ${supervisorAction} synkrone_${bot.id}`);
    }

    // Mettre à jour le statut en DB
    const newStatus = action === "stop" ? "OFFLINE" : action === "start" ? "ONLINE" : bot.status;
    await prisma.bot.update({ where: { id: bot.id }, data: { status: newStatus } });

    return NextResponse.json({ success: true, status: newStatus });
  } catch (error) {
    console.error(`Erreur action ${action} bot ${bot.id}:`, error);
    return NextResponse.json({ error: "Erreur lors de l'action" }, { status: 500 });
  }
}
