import dotenv from "dotenv";
dotenv.config({ path: ".env.local" });

import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const commands = [
  { id: "moderation.ban", name: "Ban", description: "Bannit un membre avec raison optionnelle.", category: "MODERATION", module: "moderation", priceKr: 15, usage: "{prefix}ban @user [raison]", permissions: { user: ["ban_members"], bot: ["ban_members", "send_messages"] }, envVars: [{ name: "MOD_LOG_CHANNEL_ID", description: "Salon des logs de modération", required: false }] },
  { id: "moderation.kick", name: "Kick", description: "Expulse un membre du serveur.", category: "MODERATION", module: "moderation", priceKr: 15, usage: "{prefix}kick @user [raison]", permissions: { user: ["kick_members"], bot: ["kick_members"] }, envVars: [] },
  { id: "moderation.mute", name: "Mute", description: "Met en sourdine un membre.", category: "MODERATION", module: "moderation", priceKr: 15, usage: "{prefix}mute @user [durée]", permissions: { user: ["moderate_members"], bot: ["moderate_members"] }, envVars: [] },
  { id: "moderation.warn", name: "Warn", description: "Avertit un membre.", category: "MODERATION", module: "moderation", priceKr: 10, usage: "{prefix}warn @user [raison]", permissions: { user: ["manage_messages"], bot: ["send_messages"] }, envVars: [] },
  { id: "moderation.slowmode", name: "Slowmode", description: "Active le mode lent sur un salon.", category: "MODERATION", module: "moderation", priceKr: 5, usage: "{prefix}slowmode [secondes]", permissions: { user: ["manage_channels"], bot: ["manage_channels"] }, envVars: [] },
  { id: "moderation.purge", name: "Purge", description: "Supprime N messages.", category: "MODERATION", module: "moderation", priceKr: 10, usage: "{prefix}purge [nombre]", permissions: { user: ["manage_messages"], bot: ["manage_messages"] }, envVars: [] },
  { id: "fun.poll", name: "Poll", description: "Crée un sondage.", category: "FUN", module: "fun", priceKr: 10, usage: "{prefix}poll [question]", permissions: { user: [], bot: ["send_messages", "add_reactions"] }, envVars: [] },
  { id: "fun.roulette", name: "Roulette", description: "Roulette russe Discord.", category: "FUN", module: "fun", priceKr: 10, usage: "{prefix}roulette", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "utility.ping", name: "Ping", description: "Affiche la latence du bot.", category: "UTILITY", module: "utility", priceKr: 5, usage: "{prefix}ping", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "utility.serverinfo", name: "Serverinfo", description: "Informations sur le serveur.", category: "UTILITY", module: "utility", priceKr: 5, usage: "{prefix}serverinfo", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "economy.balance", name: "Balance", description: "Affiche le solde.", category: "ECONOMY", module: "economy", priceKr: 20, usage: "{prefix}balance", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "economy.work", name: "Work", description: "Travaille pour gagner des pièces.", category: "ECONOMY", module: "economy", priceKr: 20, usage: "{prefix}work", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "xp.rank", name: "Rank", description: "Affiche le rang XP.", category: "XP", module: "xp", priceKr: 20, usage: "{prefix}rank [@user]", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "music", name: "Module Musique", description: "Lecture de musique complète.", category: "MUSIC", module: "music", priceKr: 200, usage: "{prefix}play [url/titre]", permissions: { user: [], bot: ["connect", "speak"] }, envVars: [{ name: "MUSIC_CHANNEL_ID", description: "Salon textuel dédié à la musique", required: false }] },
  { id: "ai", name: "Module IA/Chatbot", description: "Réponses IA et génération d'images.", category: "AI", module: "ai", priceKr: 300, usage: "{prefix}ask [question]", permissions: { user: [], bot: ["send_messages"] }, envVars: [{ name: "OPENAI_API_KEY", description: "Clé API OpenAI", required: true }] },
  { id: "welcome", name: "Bienvenue / Au Revoir", description: "Messages de bienvenue et rôle automatique.", category: "WELCOME", module: "welcome", priceKr: 30, usage: "Automatique", permissions: { user: ["manage_roles"], bot: ["manage_roles", "send_messages"] }, envVars: [{ name: "WELCOME_CHANNEL_ID", description: "Salon de bienvenue", required: true }] },
  { id: "tickets", name: "Système de Tickets", description: "Création et gestion de tickets.", category: "TICKETS", module: "tickets", priceKr: 50, usage: "{prefix}ticket", permissions: { user: [], bot: ["manage_channels", "send_messages"] }, envVars: [{ name: "TICKET_CATEGORY_ID", description: "Catégorie des tickets", required: true }] },
  { id: "giveaways", name: "Giveaways", description: "Création et gestion de giveaways.", category: "GIVEAWAYS", module: "giveaways", priceKr: 40, usage: "{prefix}gstart", permissions: { user: ["manage_messages"], bot: ["send_messages", "add_reactions"] }, envVars: [] },
  { id: "logs", name: "Logs", description: "Logs de modération et d'activité.", category: "LOGS", module: "logs", priceKr: 30, usage: "Automatique", permissions: { user: [], bot: ["view_audit_log", "send_messages"] }, envVars: [{ name: "LOG_CHANNEL_ID", description: "Salon des logs", required: true }] },
  { id: "autoroles", name: "Auto-Rôles", description: "Attribution automatique de rôles.", category: "AUTOROLES", module: "autoroles", priceKr: 40, usage: "Automatique", permissions: { user: ["manage_roles"], bot: ["manage_roles"] }, envVars: [] },
  { id: "reactions", name: "Reaction Roles", description: "Rôles par réaction sur des messages.", category: "REACTIONS", module: "reactions", priceKr: 30, usage: "{prefix}reactionrole", permissions: { user: ["manage_roles"], bot: ["manage_roles", "add_reactions"] }, envVars: [] },
];

async function main() {
  console.log("Seeding CommandDefinitions...");
  for (const cmd of commands) {
    await prisma.commandDefinition.upsert({
      where: { id: cmd.id },
      update: cmd,
      create: cmd,
    });
  }
  console.log(`${commands.length} commandes seedees.`);
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
