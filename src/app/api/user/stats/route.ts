import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/* GET /api/user/stats — stats enrichies de l'utilisateur connecté */
export async function GET() {
  const session = await auth();
  if (!session?.user?.dbId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const userId = session.user.dbId as string;

  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: {
      bots: { include: { stats: true } },
      minecraftServers: true,
      transactions: { orderBy: { createdAt: "desc" }, take: 10 },
      _count: { select: { bots: true, minecraftServers: true, transactions: true } },
    },
  });

  if (!user) return NextResponse.json({ error: "Introuvable" }, { status: 404 });

  const botsOnline = user.bots.filter((b) => b.status === "ONLINE").length;
  const mcOnline = user.minecraftServers.filter((s) => s.status === "ONLINE").length;
  const totalCommands = user.bots.reduce((sum, b) => sum + (b.stats?.commandsTotal ?? 0), 0);

  // Débit mensuel estimé
  const now = new Date();
  const monthAgo = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
  const monthlyTx = user.transactions.filter((t) => t.createdAt >= monthAgo);
  const krSpentMonth = monthlyTx.filter((t) => t.amount < 0).reduce((s, t) => s + Math.abs(t.amount), 0);
  const krEarnedMonth = monthlyTx.filter((t) => t.amount > 0).reduce((s, t) => s + t.amount, 0);

  return NextResponse.json({
    kronesBalance: user.kronesBalance,
    kronesSpent: user.kronesSpent,
    krSpentMonth,
    krEarnedMonth,
    bots: {
      total: user._count.bots,
      online: botsOnline,
      commandsUsed: totalCommands,
    },
    minecraft: {
      total: user._count.minecraftServers,
      online: mcOnline,
    },
    transactions: user.transactions.map((t) => ({
      id: t.id,
      amount: t.amount,
      reason: t.reason,
      createdAt: t.createdAt,
    })),
  });
}
