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

  const isUnlimited = hasUnlimitedTokens(user.roles as string[]);

  if (!isUnlimited && user.kronesBalance < totalCost) {
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

    // Récupérer les modules des cogs achetés
    const boughtCmds = await prisma.commandDefinition.findMany({
      where: { id: { in: cogs } },
    });
    const boughtModules = new Set(
      boughtCmds.map((c) => (c.module.startsWith("cogs.") ? c.module : `cogs.${c.module}`))
    );

    function shouldCopy(relPath: string): boolean {
      // Toujours copier hors de cogs/
      if (!relPath.startsWith("cogs/")) return true;
      // Toujours copier cogs/__init__.py
      if (relPath === "cogs/__init__.py") return true;

      const modPath = relPath.replace(/\//g, ".").replace(/\.py$/, "");

      // __init__.py dans un sous-dossier → copier si un cog acheté passe par là
      if (relPath.endsWith("/__init__.py")) {
        const prefix = modPath;
        for (const mod of boughtModules) {
          if (mod.startsWith(prefix + ".")) return true;
        }
        return false;
      }

      // Fichier .py dans cogs/ → copier seulement si acheté
      return boughtModules.has(modPath);
    }

    // Copier le template filtré
    try {
      const templateFiles = await fs.readdir(TEMPLATES_DIR, { recursive: true, withFileTypes: true });
      for (const entry of templateFiles) {
        if (entry.isDirectory()) continue;
        const src = path.join(TEMPLATES_DIR, entry.parentPath ? path.join(entry.parentPath, entry.name) : entry.name);
        const rel = path.relative(TEMPLATES_DIR, src);
        if (!shouldCopy(rel)) continue;
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

    // Écrire le fichier .env (lu par python-dotenv dans main.py)
    const botOwner = session.user?.name ?? "Synkrone";
    const supportUrl = process.env.SUPPORT_URL ?? "https://discord.gg/p768u2Pgp3";
    const envContent = `DISCORD_TOKEN=${botToken}\nPREFIX=${prefix}\nBOT_NAME=${botName}\nBOT_OWNER=${botOwner}\nSUPPORT_URL=${supportUrl}\n`;
    const envPath = path.join(botDir, ".env");
    await fs.writeFile(envPath, envContent, { mode: 0o600 });

    // Mettre à jour l'entrée DB avec les chemins
    await prisma.bot.update({
      where: { id: bot.id },
      data: {
        encPath: envPath,
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

    // Débiter les Kr (sauf pour admin/dev)
    if (!isUnlimited) {
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
    }

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
