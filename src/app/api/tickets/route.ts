import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { hasDevAccess } from "@/lib/roles";
import { NextResponse } from "next/server";

/* GET /api/tickets — liste mes tickets (ou tous si staff) */
export async function GET() {
  const session = await auth();
  if (!session?.user?.dbId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const userId = session.user.dbId as string;
  const isStaff = hasDevAccess(session.user.roles as string[]);

  const tickets = await prisma.ticket.findMany({
    where: isStaff ? undefined : { userId },
    include: { messages: { orderBy: { createdAt: "asc" } } },
    orderBy: { updatedAt: "desc" },
  });

  return NextResponse.json(tickets);
}

/* POST /api/tickets — créer un ticket */
export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.dbId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const userId = session.user.dbId as string;
  const { title, description, category, priority } = await req.json();

  if (!title?.trim() || !description?.trim()) {
    return NextResponse.json({ error: "Titre et description requis" }, { status: 400 });
  }

  const ticket = await prisma.ticket.create({
    data: {
      userId,
      title: title.trim(),
      description: description.trim(),
      category: category?.toUpperCase() ?? "GENERAL",
      priority: priority?.toUpperCase() ?? "MEDIUM",
    },
    include: { messages: true },
  });

  return NextResponse.json(ticket);
}
