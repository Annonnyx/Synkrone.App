import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const BOXES_PATH = process.env.VPS_BOXES_PATH ?? "/Partage/Synkrone/boxes";

export async function GET(_: Request, { params }: { params: Promise<{ userId: string }> }) {
  const { userId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  try {
    const userDir = path.join(BOXES_PATH, userId);
    await fs.mkdir(userDir, { recursive: true });
    const entries = await fs.readdir(userDir, { withFileTypes: true });

    let totalSize = 0;
    const files = [];

    for (const entry of entries) {
      if (entry.isDirectory()) continue;
      const stat = await fs.stat(path.join(userDir, entry.name));
      totalSize += Math.ceil(stat.size / (1024 * 1024));
      files.push({
        name: entry.name,
        size: stat.size,
        mtime: stat.mtime.toISOString(),
      });
    }

    return NextResponse.json({ files, totalSize });
  } catch (error) {
    console.error("Erreur lecture box:", error);
    return NextResponse.json({ error: "Erreur de lecture" }, { status: 500 });
  }
}

export async function DELETE(req: Request, { params }: { params: Promise<{ userId: string }> }) {
  const { userId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const { filename } = await req.json();
  if (!filename) {
    return NextResponse.json({ error: "Nom de fichier manquant" }, { status: 400 });
  }

  try {
    const filePath = path.join(BOXES_PATH, userId, filename);
    const resolved = path.resolve(filePath);
    const resolvedDir = path.resolve(path.join(BOXES_PATH, userId));
    if (!resolved.startsWith(resolvedDir)) {
      return NextResponse.json({ error: "Chemin invalide" }, { status: 400 });
    }

    await fs.unlink(resolved);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Erreur suppression fichier:", error);
    return NextResponse.json({ error: "Erreur de suppression" }, { status: 500 });
  }
}
