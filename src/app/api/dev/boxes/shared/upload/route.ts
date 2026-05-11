import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const SHARED_BOX_PATH = process.env.VPS_BOXES_PATH ?? "/Partage/Synkrone/boxes";
const SHARED_DIR = path.join(SHARED_BOX_PATH, "shared");
const META_PATH = path.join(SHARED_DIR, ".box-meta.json");
const TOTAL_QUOTA_MB = 20 * 1024; // 20 Go

async function readMeta(): Promise<Record<string, { owner: string; uploadedAt: string }>> {
  try {
    const raw = await fs.readFile(META_PATH, "utf-8");
    return JSON.parse(raw).files ?? {};
  } catch {
    return {};
  }
}

async function writeMeta(meta: Record<string, { owner: string; uploadedAt: string }>) {
  await fs.writeFile(META_PATH, JSON.stringify({ files: meta }, null, 2));
}

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const username = session.user.name ?? "Anonyme";

  try {
    const formData = await req.formData();
    const file = formData.get("file") as File | null;

    if (!file || !(file instanceof File)) {
      return NextResponse.json({ error: "Aucun fichier fourni" }, { status: 400 });
    }

    // Vérifier le quota
    await fs.mkdir(SHARED_DIR, { recursive: true });
    const entries = await fs.readdir(SHARED_DIR, { withFileTypes: true });
    let totalSize = 0;
    for (const entry of entries) {
      if (entry.isDirectory()) continue;
      if (entry.name === ".box-meta.json") continue;
      const stat = await fs.stat(path.join(SHARED_DIR, entry.name));
      totalSize += stat.size;
    }

    if (totalSize + file.size > TOTAL_QUOTA_MB * 1024 * 1024) {
      return NextResponse.json({ error: "Quota dépassé (20 Go)" }, { status: 413 });
    }

    const filePath = path.join(SHARED_DIR, file.name);
    const resolved = path.resolve(filePath);
    const resolvedDir = path.resolve(SHARED_DIR);
    if (!resolved.startsWith(resolvedDir)) {
      return NextResponse.json({ error: "Nom de fichier invalide" }, { status: 400 });
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    await fs.writeFile(resolved, buffer);

    // Mettre à jour les métadonnées
    const meta = await readMeta();
    meta[file.name] = { owner: username, uploadedAt: new Date().toISOString() };
    await writeMeta(meta);

    return NextResponse.json({ success: true, filename: file.name });
  } catch (error) {
    console.error("Erreur upload box partagée:", error);
    return NextResponse.json({ error: "Erreur lors de l'upload" }, { status: 500 });
  }
}
