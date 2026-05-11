import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json(
    { error: "Ce endpoint nécessite une connexion WebSocket. Utilisez le serveur custom (src/server.ts)." },
    { status: 426 }
  );
}
