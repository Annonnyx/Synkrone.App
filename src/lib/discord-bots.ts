import { Bot, Wrench, Layers, Dices } from "lucide-react";
import { LucideIcon } from "lucide-react";

export interface BotCommand {
  category: string;
  cmds: string[];
}

export interface DiscordBot {
  slug: string;
  name: string;
  tag: string;
  desc: string;
  longDesc: string;
  color: string;
  icon: LucideIcon;
  invite: string;
  support: string;
  vote?: string;
  features: string[];
  commands: BotCommand[];
}

export const discordBots: DiscordBot[] = [
  {
    slug: "vex",
    name: "Vex",
    tag: "Multifonction",
    desc: "Le bot principal de Synkrone. Modération, utilitaires, économie et plus encore.",
    longDesc:
      "Vex est le cœur de l'écosystème Synkrone. Conçu pour être l'allié indispensable de votre serveur Discord, il combine modération avancée, économie complète, utilitaires pratiques et commandes fun. Un seul bot pour tout gérer.",
    color: "indigo",
    icon: Bot,
    invite: "https://discord.com/oauth2/authorize?client_id=1368234765638963261",
    support: "https://discord.gg/p768u2Pgp3",
    vote: "https://top.gg/fr/bot/1367891720871874560",
    features: [
      "Modération complète : ban, kick, mute, warn, clear, lock/unlock",
      "Économie serveur : daily, balance, pay, leaderboard, work, shop",
      "Utilitaires : userinfo, serverinfo, avatar, poll, remind, weather",
      "Fun : memes, 8ball, roll, blagues, facts, anime",
      "Système de niveaux et récompenses d'activité",
      "Logs d'audit automatiques",
    ],
    commands: [
      { category: "Modération", cmds: ["/kick", "/ban", "/timeout", "/mute", "/warn", "/clear", "/lock", "/unlock"] },
      { category: "Utilitaires", cmds: ["/userinfo", "/serverinfo", "/avatar", "/poll", "/remind", "/weather", "/translate"] },
      { category: "Économie", cmds: ["/daily", "/balance", "/pay", "/leaderboard", "/work", "/rob", "/shop"] },
      { category: "Fun", cmds: ["/meme", "/8ball", "/roll", "/joke", "/fact", "/anime"] },
    ],
  },
  {
    slug: "asuna",
    name: "Asuna",
    tag: "Modération",
    desc: "Gestion complète de votre serveur Discord. Création de salons et rôles, modération avancée, purge et backup.",
    longDesc:
      "Asuna est dédiée à la gestion et à la sécurité de votre serveur. Elle offre des outils de modération granulaires, la gestion complète des salons et rôles, ainsi qu'un système de backup automatique pour ne jamais perdre votre configuration.",
    color: "cyan",
    icon: Wrench,
    invite: "https://discord.com/oauth2/authorize?client_id=1428865683986452640",
    support: "https://discord.gg/p768u2Pgp3",
    features: [
      "Modération avancée : ban, kick, mute, warn, notes, modlog, case ID",
      "Gestion des salons : création, suppression, clone, catégories, slowmode",
      "Gestion des rôles : création, suppression, attribution, autorole",
      "Système de backup complet : créer, charger, lister, supprimer",
      "Purge intelligente avec filtres",
      "Anti-raid et protection configurable",
    ],
    commands: [
      { category: "Modération", cmds: ["/ban", "/kick", "/mute", "/warn", "/notes", "/modlog", "/case"] },
      { category: "Salons", cmds: ["/createchannel", "/deletechannel", "/clonechannel", "/setcategory", "/slowmode"] },
      { category: "Rôles", cmds: ["/createrole", "/deleterole", "/addrole", "/removerole", "/autorole"] },
      { category: "Backup", cmds: ["/backup create", "/backup load", "/backup list", "/backup delete"] },
    ],
  },
  {
    slug: "kayaba",
    name: "Kayaba",
    tag: "Utilitaires",
    desc: "Collection de cartes, marché communautaire, échanges sécurisés et duels tour par tour.",
    longDesc:
      "Kayaba est un bot de collection et de trading. Ouvrez des packs, collectionnez des cartes uniques, échangez avec la communauté sur le marché sécurisé et affrontez d'autres joueurs en duels stratégiques tour par tour.",
    color: "amber",
    icon: Layers,
    invite: "https://discord.com/oauth2/authorize?client_id=1385913159717621780",
    support: "https://discord.gg/p768u2Pgp3",
    features: [
      "Système de gacha : packs quotidiens, cartes de raretés variées",
      "Collection et inventaire personnel complet",
      "Marché communautaire : acheter, vendre, enchères",
      "Système d'échanges sécurisés entre joueurs",
      "Duels tour par tour avec stratégie de deck",
      "Classement global et saisons",
    ],
    commands: [
      { category: "Collection", cmds: ["/card", "/inventory", "/collection", "/gacha", "/claim", "/upgrade"] },
      { category: "Marché", cmds: ["/market list", "/market buy", "/market sell", "/market search", "/auction"] },
      { category: "Échanges", cmds: ["/trade", "/trade accept", "/trade decline", "/gift"] },
      { category: "Duels", cmds: ["/duel", "/duel ranked", "/ranking", "/team create"] },
    ],
  },
  {
    slug: "yui",
    name: "Yui",
    tag: "Fun & Jeux",
    desc: "Casino complet : machine à sous, mines, blackjack, roulette, coffres scellés et pièce double ou rien.",
    longDesc:
      "Yui transforme votre serveur en casino virtuel. Des jeux classiques comme le blackjack et la roulette aux mini-jeux addictifs comme les mines et les coffres scellés, elle offre une expérience de jeu complète avec économie intégrée.",
    color: "rose",
    icon: Dices,
    invite: "https://discord.com/oauth2/authorize?client_id=1460012999912853810",
    support: "https://discord.gg/p768u2Pgp3",
    features: [
      "Casino complet : slots, mines, blackjack, roulette, coinflip, jackpot",
      "Système de coffres scellés avec loot varié",
      "Économie de jeu : daily rewards, transferts, paris",
      "Jeux rapides : pierre-feuille-ciseaux, trivia, hilo",
      "Leaderboard de gains et streaks",
      "Système de niveaux de joueur",
    ],
    commands: [
      { category: "Casino", cmds: ["/slots", "/mines", "/blackjack", "/roulette", "/coinflip", "/jackpot"] },
      { category: "Coffres", cmds: ["/coffre", "/coffre ouvrir", "/coffre liste", "/coffre échanger"] },
      { category: "Économie", cmds: ["/balance", "/daily", "/pay", "/leaderboard", "/bet"] },
      { category: "Fun", cmds: ["/roll", "/rps", "/trivia", "/hilo"] },
    ],
  },
];

export function getBotBySlug(slug: string): DiscordBot | undefined {
  return discordBots.find((b) => b.slug === slug);
}
