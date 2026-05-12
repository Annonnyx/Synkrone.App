import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import { exec } from "child_process";
import { promisify } from "util";
import { hasUnlimitedTokens } from "@/lib/roles";

const execAsync = promisify(exec);
const BOTS_PATH = process.env.VPS_BOTS_PATH ?? "/bots";
const SHARED_PATH = process.env.VPS_SHARED_PATH ?? "/Partage/Synkrone";
const TEMPLATES_DIR = `${SHARED_PATH}/templates`;

export async function POST(req: Request, { params }: { params: Promise<{ botId: string }> }) {
  const { botId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });

  const user = await prisma.user.findUnique({ where: { discordId: session.user.discordId } });
  if (!user) return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });

  const bot = await prisma.bot.findUnique({ where: { id: botId } });
  if (!bot || bot.userId !== user.id) return NextResponse.json({ error: "Bot introuvable" }, { status: 404 });

  const { commandId } = await req.json();
  if (!commandId) return NextResponse.json({ error: "commandId requis" }, { status: 400 });

  const cmdDef = await prisma.commandDefinition.findUnique({ where: { id: commandId } });
  if (!cmdDef) return NextResponse.json({ error: "Commande introuvable" }, { status: 404 });

  const currentCogs = (bot.cogs as string[]) ?? [];
  if (currentCogs.includes(commandId)) {
    return NextResponse.json({ error: "Module déjà activé" }, { status: 400 });
  }

  const isUnlimited = hasUnlimitedTokens(user.roles as string[]);

  if (!isUnlimited && user.kronesBalance < cmdDef.priceKr) {
    return NextResponse.json({ error: "Solde Kr insuffisant" }, { status: 402 });
  }

  const newCogs = [...currentCogs, commandId];
  const botDir = bot.dirPath ?? path.join(BOTS_PATH, `synkrone_${bot.id}`);

  try {
    // Mettre à jour la DB
    const txOps: any[] = [
      prisma.bot.update({
        where: { id: bot.id },
        data: {
          cogs: newCogs,
          kronesConsumed: { increment: cmdDef.priceKr },
        },
      }),
    ];

    if (!isUnlimited) {
      txOps.push(
        prisma.user.update({
          where: { id: user.id },
          data: {
            kronesBalance: { decrement: cmdDef.priceKr },
            kronesSpent: { increment: cmdDef.priceKr },
          },
        }),
        prisma.kroneTransaction.create({
          data: {
            userId: user.id,
            amount: -cmdDef.priceKr,
            reason: "BOT_UPGRADE",
            relatedId: bot.id,
          },
        })
      );
    }

    await prisma.$transaction(txOps);

    // Copier le nouveau cog dans le dossier du bot
    const modulePath = cmdDef.module.startsWith("cogs.") ? cmdDef.module : `cogs.${cmdDef.module}`;
    const relPath = modulePath.replace(/\./g, "/") + ".py";
    const src = path.join(TEMPLATES_DIR, relPath);
    const dst = path.join(botDir, relPath);

    try {
      await fs.mkdir(path.dirname(dst), { recursive: true });
      await fs.copyFile(src, dst);
    } catch {
      // Le fichier source n'existe peut-être pas (template incomplet)
    }

    // Redémarrer le bot si en ligne
    if (process.env.NODE_ENV === "production" && bot.status === "ONLINE") {
      try {
        await execAsync(`pm2 restart synkrone_${bot.id}`);
      } catch {
        // Ignorer si le bot n'est pas dans PM2
      }
    }

    return NextResponse.json({ success: true, priceKr: cmdDef.priceKr });
  } catch (error) {
    console.error("Erreur ajout module:", error);
    return NextResponse.json({ error: "Erreur lors de l'ajout du module" }, { status: 500 });
  }
}
