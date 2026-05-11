import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

// Route publique : retourne toutes les commandes disponibles pour l'affichage dans le wizard
export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const category = searchParams.get("category");

  const commands = await prisma.commandDefinition.findMany({
    where: category ? { category: category.toUpperCase() } : undefined,
    orderBy: [{ category: "asc" }, { priceKr: "asc" }],
  });

  return NextResponse.json(commands);
}
