import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import crypto from "crypto";
import { exec } from "child_process";
import { promisify } from "util";
import { hasUnlimitedTokens } from "@/lib/roles";

const execAsync = promisify(exec);
const MC_PATH = process.env.VPS_MC_PATH ?? "/mc";

function generatePassword(): string {
  return crypto.randomBytes(12).toString("base64url");
}

function encryptPassword(password: string): string {
  // Chiffrement AES-256-GCM simple (en production, utiliser une vraie clé depuis les env)
  const key = Buffer.from((process.env.NEXTAUTH_SECRET ?? "changeme").padEnd(32).slice(0, 32));
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  const encrypted = Buffer.concat([cipher.update(password, "utf8"), cipher.final()]);
  const tag = cipher.getAuthTag();
  return `${iv.toString("hex")}:${tag.toString("hex")}:${encrypted.toString("hex")}`;
}

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });

  const { serverName, version, ramMb, gameMode, difficulty, pvp, maxPlayers } = await req.json();

  if (!serverName || !version || !ramMb) {
    return NextResponse.json({ error: "Paramètres manquants" }, { status: 400 });
  }

  const kronesPerMonth = Math.ceil(ramMb / 1024) * 50;

  const user = await prisma.user.findUnique({ where: { discordId: session.user.discordId } });
  if (!user) return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });

  const isUnlimited = hasUnlimitedTokens(user.roles as string[]);

  if (!isUnlimited && user.kronesBalance < kronesPerMonth) {
    return NextResponse.json({ error: "Solde Kr insuffisant" }, { status: 402 });
  }

  const sftpPassword = generatePassword();
  const sftpPasswordEnc = encryptPassword(sftpPassword);

  const server = await prisma.minecraftServer.create({
    data: {
      userId: user.id,
      serverName,
      version,
      ramMb,
      gameMode: gameMode ?? "SURVIVAL",
      difficulty: difficulty ?? "NORMAL",
      pvp: pvp ?? true,
      maxPlayers: maxPlayers ?? 20,
      status: "OFFLINE",
      dirPath: "",
      sftpUser: `sftp_mc_temp`,
      sftpPasswordEnc,
      pm2Name: "",
      kronesPerMonth,
    },
  });

  const serverDir = path.join(MC_PATH, `mc_${server.id}`);
  const pm2Name = `mc_${server.id}`;
  const sftpUser = `sftp_mc_${server.id}`;

  try {
    await fs.mkdir(serverDir, { recursive: true });

    // Générer server.properties
    const serverProperties = `
server-name=${serverName}
gamemode=${gameMode?.toLowerCase() ?? "survival"}
difficulty=${difficulty?.toLowerCase() ?? "normal"}
pvp=${pvp ?? true}
max-players=${maxPlayers ?? 20}
level-name=world
server-port=25565
online-mode=true
    `.trim();
    await fs.writeFile(path.join(serverDir, "server.properties"), serverProperties);

    // eula.txt
    await fs.writeFile(path.join(serverDir, "eula.txt"), "eula=true\n");

    // start.sh
    const ramMin = Math.floor(ramMb * 0.5);
    const startSh = `#!/bin/bash
cd "$(dirname "$0")"
exec /usr/bin/java \\
  -Xms${ramMin}M \\
  -Xmx${ramMb}M \\
  -XX:+UseG1GC \\
  -XX:+ParallelRefProcEnabled \\
  -XX:MaxGCPauseMillis=200 \\
  -jar server.jar nogui
`;
    await fs.writeFile(path.join(serverDir, "start.sh"), startSh, { mode: 0o755 });

    // Mettre à jour DB
    await prisma.minecraftServer.update({
      where: { id: server.id },
      data: { dirPath: serverDir, pm2Name, sftpUser },
    });

    // Enregistrer dans PM2 (en production)
    if (process.env.NODE_ENV === "production") {
      await execAsync(`cd ${serverDir} && pm2 start start.sh --name ${pm2Name}`);
    }

    // Débiter les Kr (sauf admin/dev)
    if (!isUnlimited) {
      await prisma.$transaction([
      prisma.user.update({
        where: { id: user.id },
        data: {
          kronesBalance: { decrement: kronesPerMonth },
          kronesSpent: { increment: kronesPerMonth },
        },
      }),
      prisma.kroneTransaction.create({
        data: {
          userId: user.id,
          amount: -kronesPerMonth,
          reason: "MC_CREATION",
          relatedId: server.id,
        },
      }),
      ]);
    }

    return NextResponse.json({
      success: true,
      serverId: server.id,
      sftpUser,
      sftpPassword, // Affiché une seule fois à l'utilisateur
    });
  } catch (error) {
    await prisma.minecraftServer.delete({ where: { id: server.id } }).catch(() => {});
    console.error("Erreur provisioning MC:", error);
    return NextResponse.json({ error: "Erreur lors de la création du serveur" }, { status: 500 });
  }
}
