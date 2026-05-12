import dotenv from "dotenv";
dotenv.config({ path: ".env.local" });

import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

// Prix par défaut — à ajuster selon ta politique commerciale
const commands = [
  // ─── JEUX ───
  { id: "games.2048", name: "2048", description: "Jouer au jeu 2048.", category: "JEUX", module: "public.games.2048", priceKr: 10, usage: "{prefix}2048", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "games.puissance4", name: "Puissance 4", description: "Ouvre un salon de Puissance 4.", category: "JEUX", module: "public.games.puissance4", priceKr: 10, usage: "{prefix}puissance4", permissions: { user: [], bot: ["manage_channels", "send_messages"] }, envVars: [] },
  { id: "games.morpion", name: "Morpion", description: "Ouvre un salon de Morpion.", category: "JEUX", module: "public.games.morpion", priceKr: 10, usage: "{prefix}morpion", permissions: { user: [], bot: ["manage_channels", "send_messages"] }, envVars: [] },
  { id: "games.anagram", name: "Anagram", description: "Lance une anagramme.", category: "JEUX", module: "public.games.anagram", priceKr: 5, usage: "{prefix}anagram", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "games.enigme", name: "Énigme", description: "Lance une énigme.", category: "JEUX", module: "public.games.enigme", priceKr: 5, usage: "{prefix}enigme", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "games.flags", name: "Flags", description: "Quiz sur les drapeaux du monde.", category: "JEUX", module: "public.games.flags", priceKr: 5, usage: "{prefix}flags", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "games.dice", name: "Dice", description: "Lance un dé et permet d'en ajouter.", category: "JEUX", module: "public.games.dice", priceKr: 5, usage: "{prefix}dice", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "games.coinflip", name: "Coinflip", description: "Lance une pièce : pile ou face.", category: "JEUX", module: "public.games.coinflip", priceKr: 5, usage: "{prefix}coinflip", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "games.nombre", name: "Nombre", description: "Devine un nombre entre 1 et 100.", category: "JEUX", module: "public.games.nombre", priceKr: 5, usage: "{prefix}nombre", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },

  // ─── UTILITAIRES ───
  { id: "utils.play", name: "Play", description: "Ouvre le contrôle de lecture de musique.", category: "UTILITAIRES", module: "public.utilities.play", priceKr: 15, usage: "{prefix}play", permissions: { user: [], bot: ["connect", "speak", "send_messages"] }, envVars: [] },
  { id: "utils.calc", name: "Calc", description: "Ouvre la calculatrice interactive.", category: "UTILITAIRES", module: "public.utilities.calc", priceKr: 5, usage: "{prefix}calc", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "utils.choose", name: "Choose", description: "Tirage au sort entre plusieurs propositions.", category: "UTILITAIRES", module: "public.utilities.choose", priceKr: 5, usage: "{prefix}choose opt1 opt2 ...", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "utils.font", name: "Font", description: "Change la police d'un texte.", category: "UTILITAIRES", module: "public.utilities.font", priceKr: 5, usage: "{prefix}font texte", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "utils.reverse", name: "Reverse", description: "Renverse un texte avec style.", category: "UTILITAIRES", module: "public.utilities.reverse", priceKr: 5, usage: "{prefix}reverse texte", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "utils.ascii", name: "ASCII", description: "Transforme un texte en art ASCII.", category: "UTILITAIRES", module: "public.utilities.ascii", priceKr: 5, usage: "{prefix}ascii texte", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "utils.rappel", name: "Rappel", description: "Gérez vos rappels et minuteries.", category: "UTILITAIRES", module: "public.utilities.rappel", priceKr: 5, usage: "{prefix}rappel", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "utils.snipe", name: "Snipe", description: "Affiche la dernière activité du salon.", category: "UTILITAIRES", module: "public.utilities.snipe", priceKr: 5, usage: "{prefix}snipe", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },

  // ─── SOCIAL ───
  { id: "social.hug", name: "Hug", description: "Envoie un câlin à un membre.", category: "SOCIAL", module: "public.social.hug", priceKr: 5, usage: "{prefix}hug @user", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "social.kiss", name: "Kiss", description: "Envoie un bisou à un membre.", category: "SOCIAL", module: "public.social.kiss", priceKr: 5, usage: "{prefix}kiss @user", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "social.punch", name: "Punch", description: "Frappe un membre.", category: "SOCIAL", module: "public.social.punch", priceKr: 5, usage: "{prefix}punch @user", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "social.amour", name: "Amour", description: "Calcule le pourcentage d'amour entre deux membres.", category: "SOCIAL", module: "public.social.amour", priceKr: 5, usage: "{prefix}amour @user1 @user2", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "social.rate", name: "Rate", description: "Ouvre un menu pour noter quelque chose.", category: "SOCIAL", module: "public.social.rate", priceKr: 5, usage: "{prefix}rate", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "social.meme", name: "Meme", description: "Affiche un même avec un mot clé.", category: "SOCIAL", module: "public.social.meme", priceKr: 5, usage: "{prefix}meme [mot-clé]", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },

  // ─── INFOS ───
  { id: "infos.whois", name: "Whois", description: "Affiche les informations d'un membre.", category: "INFOS", module: "public.infos.whois", priceKr: 5, usage: "{prefix}whois @user", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "infos.guild", name: "Guild", description: "Affiche les informations du serveur.", category: "INFOS", module: "public.infos.guild", priceKr: 5, usage: "{prefix}guild", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "infos.channel", name: "Channel", description: "Affiche les informations d'un salon.", category: "INFOS", module: "public.infos.channel", priceKr: 5, usage: "{prefix}channel #salon", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "infos.role", name: "Role", description: "Affiche les informations d'un rôle.", category: "INFOS", module: "public.infos.role", priceKr: 5, usage: "{prefix}role @rôle", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "infos.inviteinfo", name: "Inviteinfo", description: "Classement et profil des invitations.", category: "INFOS", module: "public.infos.inviteinfo", priceKr: 5, usage: "{prefix}inviteinfo", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "infos.everyone", name: "Everyone", description: "Stats des pings everyone/here.", category: "INFOS", module: "public.infos.everyone", priceKr: 5, usage: "{prefix}everyone", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "infos.botprofil", name: "Botprofil", description: "Affiche le profil du bot.", category: "INFOS", module: "public.infos.botprofil", priceKr: 5, usage: "{prefix}botprofil", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "infos.ping", name: "Ping", description: "Affiche la latence du bot.", category: "INFOS", module: "public.infos.ping", priceKr: 5, usage: "{prefix}ping", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },

  // ─── DIVERS ───
  { id: "misc.help", name: "Help", description: "Affiche le centre d'aide interactif.", category: "DIVERS", module: "public.misc.help", priceKr: 0, usage: "{prefix}help", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "misc.feedback", name: "Feedback", description: "Donnez votre avis sur le bot.", category: "DIVERS", module: "public.misc.feedback", priceKr: 0, usage: "{prefix}feedback", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },
  { id: "misc.sondage", name: "Sondage", description: "Crée un sondage public.", category: "DIVERS", module: "public.misc.sondage", priceKr: 5, usage: "{prefix}sondage question", permissions: { user: [], bot: ["send_messages", "add_reactions"] }, envVars: [] },

  // ─── ADDONS ───
  { id: "addons.perm", name: "Perm", description: "Affiche les permissions disponibles avec un sélecteur.", category: "ADDONS", module: "cogs.addons.perm", priceKr: 20, usage: "{prefix}perm", permissions: { user: ["administrator"], bot: ["send_messages"] }, envVars: [] },
  { id: "addons.servembed", name: "Servembed", description: "Personnaliser l'apparence des embeds du serveur.", category: "ADDONS", module: "cogs.addons.servembed", priceKr: 25, usage: "{prefix}servembed", permissions: { user: ["manage_guild"], bot: ["send_messages", "embed_links"] }, envVars: [] },
  { id: "addons.prefix", name: "Prefix", description: "Configure les préfixes de commandes du serveur.", category: "ADDONS", module: "cogs.addons.prefix", priceKr: 15, usage: "{prefix}prefix", permissions: { user: ["manage_guild"], bot: ["send_messages"] }, envVars: [] },
  { id: "addons.owner", name: "Owner", description: "Afficher ou modifier les owners enregistrés du bot.", category: "ADDONS", module: "cogs.addons.owner", priceKr: 30, usage: "{prefix}owner", permissions: { user: [], bot: ["send_messages"] }, envVars: [] },

  // ─── OWNER (réservé, prix très élevé = non achetable par défaut) ───
  { id: "owner.panelbot", name: "Panelbot", description: "Panneau de configuration technique du bot.", category: "OWNER", module: "cogs.owner.panelbot", priceKr: 999, usage: "{prefix}panelbot", permissions: { user: [], bot: ["send_messages"] }, envVars: [], premium: true },
  { id: "owner.mp", name: "MP", description: "Envoyer un message privé via le bot.", category: "OWNER", module: "cogs.owner.mp", priceKr: 999, usage: "{prefix}mp @user message", permissions: { user: [], bot: ["send_messages"] }, envVars: [], premium: true },
  { id: "owner.devstats", name: "Devstats", description: "Menu statistiques de développement.", category: "OWNER", module: "cogs.owner.devstats", priceKr: 999, usage: "{prefix}devstats", permissions: { user: [], bot: ["send_messages"] }, envVars: [], premium: true },
  { id: "owner.devembed", name: "Devembed", description: "Constructeur d'embed réservé aux développeurs.", category: "OWNER", module: "cogs.owner.devembed", priceKr: 999, usage: "{prefix}devembed", permissions: { user: [], bot: ["send_messages", "embed_links"] }, envVars: [], premium: true },
  { id: "owner.blacklist", name: "Blacklist", description: "Gérer la sécurité du bot.", category: "OWNER", module: "cogs.owner.blacklist", priceKr: 999, usage: "{prefix}blacklist", permissions: { user: [], bot: ["send_messages"] }, envVars: [], premium: true },

  // ─── STATISTIQUES ───
  { id: "stats.lvlup", name: "Lvlup", description: "Configurer le salon pour les annonces de niveau.", category: "STATISTIQUES", module: "cogs.stats.lvlup", priceKr: 20, usage: "{prefix}lvlup #salon", permissions: { user: ["manage_channels"], bot: ["send_messages"] }, envVars: [] },
  { id: "stats.profil", name: "Profil", description: "Affiche le profil détaillé de l'utilisateur.", category: "STATISTIQUES", module: "cogs.stats.profil", priceKr: 15, usage: "{prefix}profil @user", permissions: { user: [], bot: ["send_messages", "attach_files"] }, envVars: [] },
  { id: "stats.leader", name: "Leader", description: "Classement des membres du serveur.", category: "STATISTIQUES", module: "cogs.stats.leader", priceKr: 20, usage: "{prefix}leader", permissions: { user: [], bot: ["send_messages", "attach_files"] }, envVars: [] },
  { id: "stats.lvl", name: "Lvl", description: "Affiche ou gère la configuration des niveaux.", category: "STATISTIQUES", module: "cogs.stats.lvl", priceKr: 20, usage: "{prefix}lvl", permissions: { user: [], bot: ["send_messages", "attach_files"] }, envVars: [] },
  { id: "stats.stats", name: "Stats", description: "Statistiques d'activité du serveur.", category: "STATISTIQUES", module: "cogs.stats.stats", priceKr: 20, usage: "{prefix}stats", permissions: { user: [], bot: ["send_messages", "attach_files"] }, envVars: [] },
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
