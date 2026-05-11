import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const { projectName, description, siteType, technology, budget } = await req.json();

  if (!projectName || !description || !siteType || !budget) {
    return NextResponse.json({ error: "Paramètres manquants" }, { status: 400 });
  }

  const user = await prisma.user.findUnique({ where: { discordId: session.user.discordId } });
  if (!user) return NextResponse.json({ error: "Utilisateur introuvable" }, { status: 404 });

  const SERVICE_FEE = 3;

  if (user.kronesBalance < SERVICE_FEE) {
    return NextResponse.json({ error: "Solde Kr insuffisant (3 Kr requis)" }, { status: 402 });
  }

  const site = await prisma.site.create({
    data: {
      userId: user.id,
      projectName,
      description,
      siteType,
      status: "PENDING",
      kronesPerMonth: 0,
    },
  });

  await prisma.$transaction([
    prisma.user.update({
      where: { id: user.id },
      data: {
        kronesBalance: { decrement: SERVICE_FEE },
        kronesSpent: { increment: SERVICE_FEE },
      },
    }),
    prisma.kroneTransaction.create({
      data: {
        userId: user.id,
        amount: -SERVICE_FEE,
        reason: "SITE_REQUEST",
        relatedId: site.id,
      },
    }),
  ]);

  return NextResponse.json({ success: true, siteId: site.id });
}
