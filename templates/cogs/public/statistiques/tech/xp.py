import discord
from discord.ext import commands, tasks # <-- Ajout de 'tasks'
import os
import json
from pathlib import Path


# Correction : ROOT = dossier 'statistiques', DATA_DIR et RULES_PATH robustes
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT.parent.parent.parent / "data" / "pack" / "statistiques"
RULES_PATH = ROOT / "assets" / "rules.json"

# Chargement des règles
with open(RULES_PATH, encoding="utf-8") as f:
    XP_RULES = json.load(f)

def get_server_dir(server_id):
    server_dir = DATA_DIR / str(server_id)
    server_dir.mkdir(parents=True, exist_ok=True)
    return server_dir

def get_user_file(server_id, user_id):
    server_dir = get_server_dir(server_id)
    user_file = server_dir / f"{user_id}.json"
    if not user_file.exists():
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump({
                "level": 1,
                "xp": 0,
                "xp_textuel": 0,
                "xp_vocal": 0,
                "messages_envoyes": 0,
                "temps_vocal": 0  # en secondes
            }, f, ensure_ascii=False, indent=2)
    return user_file

def add_xp(server_id, user_id, amount, source="textuel"):
    user_file = get_user_file(server_id, user_id)
    with open(user_file, encoding="utf-8") as f:
        data = json.load(f)

    old_level = data.get("level", 1)
    data["xp"] = data.get("xp", 0) + amount

    if source == "textuel":
        data["xp_textuel"] = data.get("xp_textuel", 0) + amount
        data["messages_envoyes"] = data.get("messages_envoyes", 0) + 1
    elif source == "vocal":
        data["xp_vocal"] = data.get("xp_vocal", 0) + amount

    # Mise à jour du niveau
    lvl = 1
    for lvl_str, xp_req in sorted(XP_RULES.get("levels_requirements", {}).items(), key=lambda x: int(x[0])):
        if data["xp"] >= xp_req:
            data["level"] = int(lvl_str)
        else:
            break

    new_level = data["level"]

    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data, old_level, new_level

def add_vocal_time(server_id, user_id, seconds):
    user_file = get_user_file(server_id, user_id)
    with open(user_file, encoding="utf-8") as f:
        data = json.load(f)
        
    data["temps_vocal"] = data.get("temps_vocal", 0) + seconds
    
    # Calcul de l'XP vocal selon rules.json (toujours entier)
    xp_per_min = XP_RULES.get("xp_gains", {}).get("voice", {}).get("xp_per_minute", 0)
    if xp_per_min > 0:
        xp_gain = int(xp_per_min * (seconds / 60))
        data["xp"] = int(data.get("xp", 0) + xp_gain)
        data["xp_vocal"] = int(data.get("xp_vocal", 0) + xp_gain)
        
        # Mise à jour du niveau
        lvl = 1
        for lvl_str, xp_req in sorted(XP_RULES.get("levels_requirements", {}).items(), key=lambda x: int(x[0])):
            if data["xp"] >= xp_req:
                data["level"] = int(lvl_str)
            else:
                break
                
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


class XPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # On démarre la boucle officielle de discord.ext.tasks
        self.vocal_xp_task.start()

    def cog_unload(self):
        # On l'arrête proprement quand le cog est déchargé
        self.vocal_xp_task.cancel()

    @tasks.loop(seconds=60)
    async def vocal_xp_task(self):
        for guild in self.bot.guilds:
                afk_channel = guild.afk_channel
                for channel in guild.voice_channels:
                    for member in channel.members:
                        if member.bot:
                            continue
                        
                        if afk_channel and channel == afk_channel:
                            continue
                        if member.voice is None:
                            continue
                        if member.voice.deaf or member.voice.self_deaf:
                            continue
                            
                        # Si on arrive ici, l'utilisateur est valide !
                        add_vocal_time(guild.id, member.id, 10)
                        # ...print supprimé...
                        
    @vocal_xp_task.before_loop
    async def before_vocal_xp_task(self):
        # On s'assure que le bot est bien connecté avant de lancer la boucle
        await self.bot.wait_until_ready()


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild and not message.author.bot:
            xp_gain = XP_RULES.get("xp_gains", {}).get("text", {}).get("xp_per_message", 0)
            if xp_gain > 0:
                data, old_level, new_level = add_xp(message.guild.id, message.author.id, xp_gain, source="textuel")
                if new_level > old_level:
                    # Déclenche un événement personnalisé
                    self.bot.dispatch("level_up", message, old_level, new_level)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.guild and not member.bot:
            get_user_file(member.guild.id, member.id)

async def setup(bot):
    await bot.add_cog(XPCog(bot))