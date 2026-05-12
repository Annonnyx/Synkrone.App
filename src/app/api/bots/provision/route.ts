import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
const BOTS_PATH = process.env.VPS_BOTS_PATH ?? "/bots";
const SHARED_PATH = process.env.VPS_SHARED_PATH ?? "/Partage/Synkrone";
const TEMPLATE_PATH = `${SHARED_PATH}/templates/main.py`;
const TEMPLATES_DIR = `${SHARED_PATH}/templates`;

// Calcule le coût total des cogs sélectionnés
const COGS_PRICES: Record<string, number> = {
  "moderation.ban": 15, "moderation.kick": 15, "moderation.mute": 15,
  "moderation.warn": 10, "moderation.slowmode": 5, "moderation.purge": 10,
  "moderation.lock": 10, "moderation.unlock": 10,
  "fun.poll": 10, "fun.roulette": 10, "fun.8ball": 5, "fun.blague": 5,
  "utility.ping": 5, "utility.serverinfo": 5, "utility.userinfo": 5,
  "utility.embed": 10, "utility.annonce": 10,
  "economy.balance": 20, "economy.work": 20, "economy.shop": 30,
  "economy.give": 10, "economy.leaderboard": 20,
  "xp.rank": 20, "xp.leaderboard": 20, "xp.rewards": 60,
  "music": 200, "ai": 300, "welcome": 30, "tickets": 50,
  "giveaways": 40, "logs": 30, "autoroles": 40, "reactions": 30,
};

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const { botName, botToken, prefix = "!", cogs } = await req.json();

  if (!botName || !botToken || !Array.isArray(cogs)) {
    return NextResponse.json({ error: "Paramètres manquants" }, { status: 400 });
  }

  // Calcul du coût
  const totalCost = cogs.reduce((sum: number, cog: string) => {
    return sum + (COGS_PRICES[cog] ?? 0);
  }, 0);

  // Vérifier le solde
  const user = await prisma.user.findUnique({
    where: { discordId: session.user.discordId },
  });

  if (!user) {
    return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });
  }

  if (user.kronesBalance < totalCost) {
    return NextResponse.json({ error: "Solde Kr insuffisant" }, { status: 402 });
  }

  // Créer l'entrée Bot en DB
  const bot = await prisma.bot.create({
    data: {
      userId: user.id,
      botName,
      prefix,
      cogs,
      kronesConsumed: totalCost,
      status: "OFFLINE",
      encPath: "",
      dirPath: "",
    },
  });

  const botDirName = `synkrone_${bot.id}`;
  const botDir = path.join(BOTS_PATH, botDirName);

  try {
    // Créer le dossier du bot
    await fs.mkdir(botDir, { recursive: true });

    // Copier le template complet (main.py + cogs + requirements.txt)
    try {
      const templateFiles = await fs.readdir(TEMPLATES_DIR, { recursive: true, withFileTypes: true });
      for (const entry of templateFiles) {
        if (entry.isDirectory()) continue;
        const src = path.join(TEMPLATES_DIR, entry.parentPath ? path.join(entry.parentPath, entry.name) : entry.name);
        const rel = path.relative(TEMPLATES_DIR, src);
        const dst = path.join(botDir, rel);
        await fs.mkdir(path.dirname(dst), { recursive: true });
        await fs.copyFile(src, dst);
      }
    } catch {
      // Template absent en dev local, on crée un main.py minimal
      await fs.writeFile(path.join(botDir, "main.py"), `# Bot Synkrone ${botName}\nprint("Bot démarré")\n`);
    }

    // Générer bot.config.json
    const config = {
      botId: botDirName,
      botName,
      prefix,
      slashCommands: false,
      cogs,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    await fs.writeFile(
      path.join(botDir, "bot.config.json"),
      JSON.stringify(config, null, 2)
    );

    // Écrire le fichier .enc avec chmod 600
    const encContent = `BOT_TOKEN=${botToken}\nPREFIX=${prefix}\nBOT_NAME=${botName}\n`;
    const encPath = path.join(botDir, ".enc");
    await fs.writeFile(encPath, encContent, { mode: 0o600 });

    // Mettre à jour l'entrée DB avec les chemins
    await prisma.bot.update({
      where: { id: bot.id },
      data: {
        encPath,
        dirPath: botDir,
      },
    });

    // Installer dépendances Python si requirements.txt existe
    if (process.env.NODE_ENV === "production") {
      const reqPath = path.join(botDir, "requirements.txt");
      try {
        await fs.access(reqPath);
        await execAsync(`pip3 install -r ${reqPath}`);
      } catch {
        // Pas de requirements.txt, on ignore
      }
      await execAsync(`cd ${botDir} && pm2 start main.py --name synkrone_${bot.id} --interpreter python3`);
    }

    // Débiter les Kr
    await prisma.$transaction([
      prisma.user.update({
        where: { id: user.id },
        data: {
          kronesBalance: { decrement: totalCost },
          kronesSpent: { increment: totalCost },
        },
      }),
      prisma.kroneTransaction.create({
        data: {
          userId: user.id,
          amount: -totalCost,
          reason: "BOT_CREATION",
          relatedId: bot.id,
        },
      }),
    ]);

    // Créer l'entrée stats
    await prisma.botStats.create({
      data: { botId: bot.id },
    });

    return NextResponse.json({ success: true, botId: bot.id });
  } catch (error) {
    // En cas d'erreur, supprimer l'entrée DB
    await prisma.bot.delete({ where: { id: bot.id } }).catch(() => {});
    console.error("Erreur provisioning bot:", error);
    return NextResponse.json({ error: "Erreur lors de la création du bot" }, { status: 500 });
  }
}
