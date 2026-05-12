import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { hasDevAccess } from "@/lib/roles";
import { NextResponse } from "next/server";

/* GET /api/tickets/:id */
export async function GET(_: Request, { params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  const session = await auth();
  if (!session?.user?.dbId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const ticket = await prisma.ticket.findUnique({
    where: { id: ticketId },
    include: { messages: { orderBy: { createdAt: "asc" } } },
  });

  if (!ticket) return NextResponse.json({ error: "Introuvable" }, { status: 404 });

  const isStaff = hasDevAccess(session.user.roles as string[]);
  if (!isStaff && ticket.userId !== session.user.dbId) {
    return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
  }

  return NextResponse.json(ticket);
}

/* PATCH /api/tickets/:id — mise à jour statut / assignation */
export async function PATCH(req: Request, { params }: { params: Promise<{ ticketId: string }> }) {
  const { ticketId } = await params;
  const session = await auth();
  if (!session?.user?.dbId) return NextResponse.json({ error: "Non authentifié" }, { status: 401 });

  const isStaff = hasDevAccess(session.user.roles as string[]);
  const ticket = await prisma.ticket.findUnique({ where: { id: ticketId } });
  if (!ticket) return NextResponse.json({ error: "Introuvable" }, { status: 404 });

  if (!isStaff && ticket.userId !== session.user.dbId) {
    return NextResponse.json({ error: "Accès refusé" }, { status: 403 });
  }

  const body = await req.json();
  const data: any = {};

  if (body.status && ["OPEN", "PENDING", "RESOLVED", "CLOSED"].includes(body.status)) {
    data.status = body.status;
  }
  if (isStaff && body.assignedTo) data.assignedTo = body.assignedTo;
  if (isStaff && body.priority) data.priority = body.priority;

  const updated = await prisma.ticket.update({
    where: { id: ticketId },
    data,
    include: { messages: { orderBy: { createdAt: "asc" } } },
  });

  return NextResponse.json(updated);
}
