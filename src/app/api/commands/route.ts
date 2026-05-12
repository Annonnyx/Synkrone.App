import { NextResponse } from "next/server";
import { scanCogs } from "@/lib/cog-catalog";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const category = searchParams.get("category");

  const commands = await scanCogs();

  if (category) {
    return NextResponse.json(
      commands.filter((c) => c.category === category.toUpperCase())
    );
  }

  return NextResponse.json(commands);
}
