import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { hasRole } from "@/lib/roles";
import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const BOXES_PATH = process.env.VPS_BOXES_PATH ?? "/Partage/Synkrone/boxes";

function resolveSafe(baseDir: string, relativePath: string): string {
  const resolved = path.resolve(path.join(baseDir, relativePath));
  const resolvedBase = path.resolve(baseDir);
  if (!resolved.startsWith(resolvedBase)) {
    throw new Error("Chemin invalide");
  }
  return resolved;
}

async function requireManager(session: any) {
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }
  const user = await prisma.user.findUnique({
    where: { discordId: session.user.discordId },
  });
  if (!user || !hasRole(user.roles, "MANAGER")) {
    return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
  }
  return null;
}

// GET — lister le contenu d'un dossier
export async function GET(req: Request) {
  const session = await auth();
  const denied = await requireManager(session);
  if (denied) return denied;

  const { searchParams } = new URL(req.url);
  const userId = searchParams.get("userId");
  const relativePath = searchParams.get("path") ?? "";

  if (!userId) {
    return NextResponse.json({ error: "userId manquant" }, { status: 400 });
  }

  try {
    const baseDir = path.join(BOXES_PATH, userId);
    const targetDir = resolveSafe(baseDir, relativePath);
    await fs.mkdir(targetDir, { recursive: true });

    const entries = await fs.readdir(targetDir, { withFileTypes: true });
    const items = [];
    let totalSize = 0;

    for (const entry of entries) {
      const entryPath = path.join(targetDir, entry.name);
      const stat = await fs.stat(entryPath);
      const item = {
        name: entry.name,
        type: entry.isDirectory() ? "directory" : "file",
        size: entry.isDirectory() ? 0 : stat.size,
        mtime: stat.mtime.toISOString(),
      };
      items.push(item);
      if (!entry.isDirectory()) {
        totalSize += stat.size;
      }
    }

    // Tri : dossiers d'abord, puis fichiers par nom
    items.sort((a, b) => {
      if (a.type === b.type) return a.name.localeCompare(b.name);
      return a.type === "directory" ? -1 : 1;
    });

    return NextResponse.json({
      items,
      totalSize,
      path: relativePath,
    });
  } catch (error) {
    console.error("Erreur lecture box:", error);
    return NextResponse.json(
      { error: "Erreur de lecture" },
      { status: 500 }
    );
  }
}

// POST — créer un dossier ou uploader un fichier
export async function POST(req: Request) {
  const session = await auth();
  const denied = await requireManager(session);
  if (denied) return denied;

  const contentType = req.headers.get("content-type") ?? "";

  // Upload de fichier (multipart/form-data)
  if (contentType.includes("multipart/form-data")) {
    const { searchParams } = new URL(req.url);
    const userId = searchParams.get("userId");
    const relativePath = searchParams.get("path") ?? "";

    if (!userId) {
      return NextResponse.json({ error: "userId manquant" }, { status: 400 });
    }

    try {
      const formData = await req.formData();
      const file = formData.get("file") as File | null;
      if (!file || !(file instanceof File)) {
        return NextResponse.json({ error: "Aucun fichier fourni" }, { status: 400 });
      }

      const baseDir = path.join(BOXES_PATH, userId);
      const targetDir = resolveSafe(baseDir, relativePath);
      await fs.mkdir(targetDir, { recursive: true });

      const filePath = path.join(targetDir, file.name);
      const resolved = path.resolve(filePath);
      const resolvedDir = path.resolve(targetDir);
      if (!resolved.startsWith(resolvedDir)) {
        return NextResponse.json({ error: "Nom de fichier invalide" }, { status: 400 });
      }

      const buffer = Buffer.from(await file.arrayBuffer());
      await fs.writeFile(resolved, buffer);

      return NextResponse.json({ success: true, filename: file.name });
    } catch (error) {
      console.error("Erreur upload box:", error);
      return NextResponse.json({ error: "Erreur lors de l'upload" }, { status: 500 });
    }
  }

  // Création de dossier (JSON)
  try {
    const { userId, path: relativePath, name } = await req.json();
    if (!userId || !name) {
      return NextResponse.json({ error: "Paramètres manquants" }, { status: 400 });
    }

    const baseDir = path.join(BOXES_PATH, userId);
    const targetDir = resolveSafe(baseDir, path.join(relativePath ?? "", name));
    await fs.mkdir(targetDir, { recursive: true });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Erreur mkdir box:", error);
    return NextResponse.json({ error: "Erreur lors de la création" }, { status: 500 });
  }
}

// DELETE — supprimer un fichier ou dossier
export async function DELETE(req: Request) {
  const session = await auth();
  const denied = await requireManager(session);
  if (denied) return denied;

  try {
    const { userId, path: relativePath } = await req.json();
    if (!userId || !relativePath) {
      return NextResponse.json({ error: "Paramètres manquants" }, { status: 400 });
    }

    const baseDir = path.join(BOXES_PATH, userId);
    const targetPath = resolveSafe(baseDir, relativePath);

    const stat = await fs.stat(targetPath);
    if (stat.isDirectory()) {
      await fs.rmdir(targetPath, { recursive: true });
    } else {
      await fs.unlink(targetPath);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Erreur suppression box:", error);
    return NextResponse.json({ error: "Erreur de suppression" }, { status: 500 });
  }
}
