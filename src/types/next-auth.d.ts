import "next-auth";

declare module "next-auth" {
  interface Session {
    user: {
      name?: string | null;
      email?: string | null;
      image?: string | null;
      discordId: string;
      roles: string[];
      kronesBalance: number;
      subscriptionId: string | null;
      dbId: string;
    };
  }
}
