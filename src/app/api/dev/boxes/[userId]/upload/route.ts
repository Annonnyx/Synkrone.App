import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

const BOXES_PATH = process.env.VPS_BOXES_PATH ?? "/Partage/Synkrone/boxes";

export async function POST(req: Request, { params }: { params: Promise<{ userId: string }> }) {
  const { userId } = await params;
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  try {
    const formData = await req.formData();
    const file = formData.get("file") as File | null;

    if (!file || !(file instanceof File)) {
      return NextResponse.json({ error: "Aucun fichier fourni" }, { status: 400 });
    }

    const userDir = path.join(BOXES_PATH, userId);
    await fs.mkdir(userDir, { recursive: true });

    const filePath = path.join(userDir, file.name);
    const resolved = path.resolve(filePath);
    const resolvedDir = path.resolve(userDir);
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
