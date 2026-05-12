import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/**
 * POST /api/cron/billing
 * Appelé par un cron externe (ex: systemd timer ou Coolify cron)
 * toutes les heures pour :
 * 1. Débiter le coût mensuel (proratisé par heure) des bots et MC actifs
 * 2. Suspendre les services si solde insuffisant
 *
 * Protection : vérifie un header secret si CRON_SECRET est défini
 */
export async function POST(req: Request) {
  const secret = process.env.CRON_SECRET;
  if (secret) {
    const auth = req.headers.get("authorization");
    if (auth !== `Bearer ${secret}`) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
  }

  const suspendedBots: string[] = [];
  const suspendedServers: string[] = [];

  try {
    // ─── 1. BOTS ─────────────────────────────────────────────────────
    const activeBots = await prisma.bot.findMany({
      where: { status: { in: ["ONLINE", "RUNNING"] } },
      include: { user: true },
    });

    for (const bot of activeBots) {
      const user = bot.user;
      const costPerHour = Math.ceil(bot.kronesPerMonth / 730); // ~30 jours
      if (costPerHour <= 0) continue;

      if (user.kronesBalance < costPerHour) {
        // Solde insuffisant → suspendre
        try {
          await execAsync(`pm2 stop synkrone_${bot.id}`);
        } catch {}

        await prisma.bot.update({
          where: { id: bot.id },
          data: { status: "SUSPENDED" },
        });
        suspendedBots.push(bot.botName);
      } else {
        // Débiter
        await prisma.$transaction([
          prisma.user.update({
            where: { id: user.id },
            data: {
              kronesBalance: { decrement: costPerHour },
              kronesSpent: { increment: costPerHour },
            },
          }),
          prisma.kroneTransaction.create({
            data: {
              userId: user.id,
              amount: -costPerHour,
              reason: "BOT_HOURLY",
              relatedId: bot.id,
            },
          }),
        ]);
      }
    }

    // ─── 2. MINECRAFT ────────────────────────────────────────────────
    const activeMC = await prisma.minecraftServer.findMany({
      where: { status: { in: ["ONLINE", "RUNNING"] } },
      include: { user: true },
    });

    for (const server of activeMC) {
      const user = server.user;
      const costPerHour = Math.ceil(server.kronesPerMonth / 730);
      if (costPerHour <= 0) continue;

      if (user.kronesBalance < costPerHour) {
        try {
          await execAsync(`pm2 stop mc_${server.id}`);
        } catch {}

        await prisma.minecraftServer.update({
          where: { id: server.id },
          data: { status: "SUSPENDED" },
        });
        suspendedServers.push(server.serverName);
      } else {
        await prisma.$transaction([
          prisma.user.update({
            where: { id: user.id },
            data: {
              kronesBalance: { decrement: costPerHour },
              kronesSpent: { increment: costPerHour },
            },
          }),
          prisma.kroneTransaction.create({
            data: {
              userId: user.id,
              amount: -costPerHour,
              reason: "MC_HOURLY",
              relatedId: server.id,
            },
          }),
        ]);
      }
    }

    return NextResponse.json({
      success: true,
      checkedBots: activeBots.length,
      checkedServers: activeMC.length,
      suspendedBots,
      suspendedServers,
    });
  } catch (error) {
    console.error("Erreur cron billing:", error);
    return NextResponse.json({ error: "Billing cron failed" }, { status: 500 });
  }
}
