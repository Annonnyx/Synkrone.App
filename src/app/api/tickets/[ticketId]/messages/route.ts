import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { hasDevAccess } from "@/lib/roles";
import { NextResponse } from "next/server";

/* POST /api/tickets/:id/messages — ajouter un message */
export async function POST(req: Request, { params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  const session = await auth();
  if (!session?.user?.dbId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const ticket = await prisma.ticket.findUnique({ where: { id: ticketId } });
  if (!ticket) return NextResponse.json({ error: "Introuvable" }, { status: 404 });

  const isStaff = hasDevAccess(session.user.roles as string[]);
  if (!isStaff && ticket.userId !== session.user.dbId) {
    return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
  }

  const { content } = await req.json();
  if (!content?.trim()) {
    return NextResponse.json({ error: "Contenu requis" }, { status: 400 });
  }

  const message = await prisma.ticketMessage.create({
    data: {
      ticketId,
      authorId: session.user.dbId as string,
      authorName: session.user.name ?? "Utilisateur",
      content: content.trim(),
      isStaff,
    },
  });

  // Mettre à jour le ticket
  await prisma.ticket.update({
    where: { id: ticketId },
    data: { updatedAt: new Date() },
  });

  return NextResponse.json(message);
}
