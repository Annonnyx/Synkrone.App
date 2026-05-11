import { auth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { DISCORD_ROLE_MAP, Role } from "@/lib/roles";
import { NextResponse } from "next/server";

export async function GET() {
  const session = await auth();
  if (!session?.user?.discordId) {
    return NextResponse.json({ error: "Non authentifié" }, { status: 401 });
  }

  const discordId = session.user.discordId;
  const guildIds = [
    process.env.DISCORD_SUPPORT_GUILD_ID!,
    process.env.DISCORD_DEV_GUILD_ID!,
  ];

  const roles: Role[] = [];

  for (const guildId of guildIds) {
    try {
      const res = await fetch(
        `https://discord.com/api/v10/guilds/${guildId}/members/${discordId}`,
        { headers: { Authorization: `Bot ${process.env.DISCORD_BOT_TOKEN}` } }
      );
      if (!res.ok) continue;
      const member = await res.json();
      for (const discordRoleId of member.roles ?? []) {
        const internalRole = DISCORD_ROLE_MAP[discordRoleId];
        if (internalRole && !roles.includes(internalRole)) roles.push(internalRole);
      }
    } catch {}
  }

  const finalRoles = roles.length > 0 ? roles : (["USER"] as Role[]);

  await prisma.user.update({
    where: { discordId },
    data: { roles: finalRoles },
  });

  return NextResponse.json({ roles: finalRoles });
}
