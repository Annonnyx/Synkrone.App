import NextAuth, { NextAuthConfig } from "next-auth";
import DiscordProvider from "next-auth/providers/discord";
import { prisma } from "@/lib/prisma";
import { DISCORD_ROLE_MAP, Role } from "@/lib/roles";

// Fonction qui interroge l'API Discord Bot pour obtenir les rôles d'un utilisateur
async function fetchDiscordRoles(userId: string): Promise<Role[]> {
  const guildIds = [
    process.env.DISCORD_SUPPORT_GUILD_ID!,
    process.env.DISCORD_DEV_GUILD_ID!,
  ];

  const roles: Role[] = [];

  for (const guildId of guildIds) {
    try {
      const res = await fetch(
        `https://discord.com/api/v10/guilds/${guildId}/members/${userId}`,
        {
          headers: {
            Authorization: `Bot ${process.env.DISCORD_BOT_TOKEN}`,
          },
        }
      );

      if (!res.ok) continue;

      const member = await res.json();
      const memberRoles: string[] = member.roles ?? [];

      for (const discordRoleId of memberRoles) {
        const internalRole = DISCORD_ROLE_MAP[discordRoleId];
        if (internalRole && !roles.includes(internalRole)) {
          roles.push(internalRole);
        }
      }
    } catch {
      // Serveur inaccessible, on continue
    }
  }

  return roles.length > 0 ? roles : ["USER"];
}

export const authConfig: NextAuthConfig = {
  providers: [
    DiscordProvider({
      clientId: process.env.DISCORD_CLIENT_ID!,
      clientSecret: process.env.DISCORD_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: "identify email guilds guilds.members.read",
        },
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      try {
        if (!profile?.id || !account) {
          console.error("[Auth] Missing profile.id or account", { profile, account });
          return false;
        }

        const discordId = profile.id as string;
        const roles = await fetchDiscordRoles(discordId);

        await prisma.user.upsert({
          where: { discordId },
          update: {
            username: user.name ?? "Inconnu",
            email: user.email ?? null,
            avatar: user.image ?? null,
            roles,
            updatedAt: new Date(),
          },
          create: {
            discordId,
            username: user.name ?? "Inconnu",
            email: user.email ?? null,
            avatar: user.image ?? null,
            roles,
            kronesBalance: 1000,
          },
        });

        return true;
      } catch (err) {
        console.error("[Auth] signIn error:", err);
        return false;
      }
    },

    async jwt({ token, account, profile }) {
      if (account && profile) {
        const discordId = profile.id as string;
        token.discordId = discordId;

        const dbUser = await prisma.user.findUnique({
          where: { discordId },
        });

        token.roles = dbUser?.roles ?? ["USER"];
        token.kronesBalance = dbUser?.kronesBalance ?? 1000;
        token.subscriptionId = dbUser?.subscriptionId ?? null;
        token.dbId = dbUser?.id;
      }
      return token;
    },

    async session({ session, token }) {
      session.user.discordId = token.discordId as string;
      session.user.roles = token.roles as string[];
      session.user.kronesBalance = token.kronesBalance as number;
      session.user.subscriptionId = (token.subscriptionId as string | null) ?? null;
      session.user.dbId = token.dbId as string;
      return session;
    },
  },

  pages: {
    signIn: "/login",
    error: "/login",
  },

  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 jours
  },
};

export const { handlers, auth, signIn, signOut } = NextAuth(authConfig);
