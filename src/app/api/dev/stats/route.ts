import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { hasDevAccess } from "@/lib/roles";
import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

/* GET /api/dev/stats — stats globales pour les devs/staff */
export async function GET() {
  const session = await auth();
  if (!session?.user?.dbId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const isStaff = hasDevAccess(session.user.roles as string[]);
  if (!isStaff) {
    return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
  }

  // Compteurs globaux
  const totalUsers = await prisma.user.count();
  const totalBots = await prisma.bot.count();
  const botsOnline = await prisma.bot.count({ where: { status: "ONLINE" } });
  const totalMC = await prisma.minecraftServer.count();
  const mcOnline = await prisma.minecraftServer.count({ where: { status: "ONLINE" } });
  const totalTickets = await prisma.ticket.count();
  const openTickets = await prisma.ticket.count({ where: { status: "OPEN" } });

  // Total Kr en circulation
  const users = await prisma.user.findMany({ select: { kronesBalance: true, kronesSpent: true } });
  const totalKrBalance = users.reduce((s, u) => s + u.kronesBalance, 0);
  const totalKrSpent = users.reduce((s, u) => s + u.kronesSpent, 0);

  // CPU / RAM / Disk du VPS (si disponible)
  let cpu = null;
  let ram = null;
  let disk = null;
  try {
    const { stdout: cpuOut } = await execAsync("cat /proc/loadavg | awk '{print $1}'");
    cpu = parseFloat(cpuOut.trim());
  } catch {}
  try {
    const { stdout: memOut } = await execAsync("free -m | awk '/Mem:/ {printf \"%.1f\", $3/$2 * 100.0}'");
    ram = parseFloat(memOut.trim());
  } catch {}
  try {
    const { stdout: diskOut } = await execAsync("df -h / | awk 'NR==2 {print $5}' | sed 's/%//'");
    disk = parseInt(diskOut.trim(), 10);
  } catch {}

  return NextResponse.json({
    users: { total: totalUsers },
    bots: { total: totalBots, online: botsOnline },
    minecraft: { total: totalMC, online: mcOnline },
    tickets: { total: totalTickets, open: openTickets },
    krones: { inCirculation: totalKrBalance, totalSpent: totalKrSpent },
    vps: { cpu, ram, disk },
  });
}
