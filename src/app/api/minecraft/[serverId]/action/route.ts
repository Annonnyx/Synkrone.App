import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

export async function POST(req: Request, { params }: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });

  const { action } = await req.json();
  const validActions = ["start", "stop", "restart", "save"];
  if (!validActions.includes(action)) {
    return NextResponse.json({ error: "Action invalide" }, { status: 400 });
  }

  const user = await prisma.user.findUnique({ where: { discordId: session.user.discordId } });
  if (!user) return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });

  const server = await prisma.minecraftServer.findUnique({ where: { id: serverId } });
  if (!server || server.userId !== user.id) return NextResponse.json({ error: "Serveur introuvable" }, { status: 404 });

  try {
    if (process.env.NODE_ENV === "production" && server.pm2Name) {
      if (action === "save") {
        // Sauvegarder via console RCON ou screen
        await execAsync(`pm2 sendLogs ${server.pm2Name} "save-all"`);
      } else {
        await execAsync(`pm2 ${action === "start" ? "start" : action === "stop" ? "stop" : "restart"} ${server.pm2Name}`);
      }
    }

    const newStatus = action === "stop" ? "OFFLINE" : action === "start" ? "ONLINE" : server.status;
    await prisma.minecraftServer.update({ where: { id: server.id }, data: { status: newStatus } });

    return NextResponse.json({ success: true, status: newStatus });
  } catch (error) {
    console.error(`Erreur action ${action} MC ${server.id}:`, error);
    return NextResponse.json({ error: "Erreur lors de l'action" }, { status: 500 });
  }
}
