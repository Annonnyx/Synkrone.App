import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const { offre } = await req.json();
  const validOffers = ["starter", "basic", "pro", "studio", "enterprise"];

  if (!validOffers.includes(offre)) {
    return NextResponse.json({ error: "Offre invalide" }, { status: 400 });
  }

  // TODO: Intégrer Stripe Checkout ici
  return NextResponse.json(
    { error: "Paiement non encore implémenté. Contactez-nous sur Discord." },
    { status: 503 }
  );
}
