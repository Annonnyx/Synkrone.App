import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const SHARED_BOX_PATH = process.env.VPS_BOXES_PATH ?? "/Partage/Synkrone/boxes";
const SHARED_DIR = path.join(SHARED_BOX_PATH, "shared");
const META_PATH = path.join(SHARED_DIR, ".box-meta.json");

async function readMeta(): Promise<Record<string, { owner: string; uploadedAt: string }>> {
  try {
    const raw = await fs.readFile(META_PATH, "utf-8");
    return JSON.parse(raw).files ?? {};
  } catch {
    return {};
  }
}

async function writeMeta(meta: Record<string, { owner: string; uploadedAt: string }>) {
  await fs.mkdir(SHARED_DIR, { recursive: true });
  await fs.writeFile(META_PATH, JSON.stringify({ files: meta }, null, 2));
}

export async function GET() {
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  try {
    await fs.mkdir(SHARED_DIR, { recursive: true });
    const entries = await fs.readdir(SHARED_DIR, { withFileTypes: true });
    const meta = await readMeta();

    let totalSize = 0;
    const files = [];

    for (const entry of entries) {
      if (entry.isDirectory()) continue;
      if (entry.name === ".box-meta.json") continue;
      const stat = await fs.stat(path.join(SHARED_DIR, entry.name));
      totalSize += Math.ceil(stat.size / (1024 * 1024)); // en Mo
      files.push({
        name: entry.name,
        size: stat.size,
        mtime: stat.mtime.toISOString(),
        owner: meta[entry.name]?.owner,
      });
    }

    return NextResponse.json({ files, totalSize });
  } catch (error) {
    console.error("Erreur lecture box partagée:", error);
    return NextResponse.json({ error: "Erreur de lecture" }, { status: 500 });
  }
}

export async function DELETE(req: Request) {
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const { filename } = await req.json();
  if (!filename) {
    return NextResponse.json({ error: "Nom de fichier manquant" }, { status: 400 });
  }

  try {
    const filePath = path.join(SHARED_DIR, filename);
    const resolved = path.resolve(filePath);
    const resolvedDir = path.resolve(SHARED_DIR);
    // Sécurité : vérifier que le fichier est bien dans le dossier partagé
    if (!resolved.startsWith(resolvedDir)) {
      return NextResponse.json({ error: "Chemin invalide" }, { status: 400 });
    }

    await fs.unlink(resolved);

    // Mettre à jour le meta
    const meta = await readMeta();
    delete meta[filename];
    await writeMeta(meta);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Erreur suppression fichier partagé:", error);
    return NextResponse.json({ error: "Erreur de suppression" }, { status: 500 });
  }
}
