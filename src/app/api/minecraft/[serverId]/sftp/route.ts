import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";
import crypto from "crypto";

function decryptPassword(enc: string): string {
  try {
    const key = Buffer.from((process.env.NEXTAUTH_SECRET ?? "changeme").padEnd(32).slice(0, 32));
    const [ivHex, tagHex, encryptedHex] = enc.split(":");
    const iv = Buffer.from(ivHex, "hex");
    const tag = Buffer.from(tagHex, "hex");
    const encrypted = Buffer.from(encryptedHex, "hex");
    const decipher = crypto.createDecipheriv("aes-256-gcm", key, iv);
    decipher.setAuthTag(tag);
    const decrypted = Buffer.concat([decipher.update(encrypted), decipher.final()]);
    return decrypted.toString("utf8");
  } catch {
    return "";
  }
}

export async function GET(_: Request, { params }: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });

  const user = await prisma.user.findUnique({ where: { discordId: session.user.discordId } });
  if (!user) return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });

  const server = await prisma.minecraftServer.findUnique({ where: { id: serverId } });
  if (!server || server.userId !== user.id) return NextResponse.json({ error: "Serveur introuvable" }, { status: 404 });

  const password = decryptPassword(server.sftpPasswordEnc);
  return NextResponse.json({
    host: "synkrone.app",
    port: 22,
    user: server.sftpUser,
    password,
  });
}
