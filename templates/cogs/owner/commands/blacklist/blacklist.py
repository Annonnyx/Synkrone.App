import discord
from discord.ext import commands, tasks
import json
import asyncio
from pathlib import Path

# --- CONFIGURATION DES COULEURS (ANSI) ---
RED = "\033[31m"
RESET = "\033[0m"

# --- CONFIGURATION DES CHEMINS ---
BLACKLIST_PATH = Path(__file__).parent / "blacklist.json"

# --- UTILITAIRES ---

def get_blacklist_data():
    if not BLACKLIST_PATH.exists():
        default_data = {"users": [], "servers": []}
        try:
            with open(BLACKLIST_PATH, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=4)
            return default_data
        except: return default_data
            
    try:
        with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": [], "servers": []}

# --- COG ---

class BlacklistCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.tree.interaction_check = self.master_interaction_check
        self.bot.add_check(self.global_prefix_check)
        
        self.security_scan.start()

    def cog_unload(self):
        self.security_scan.cancel()
        self.bot.remove_check(self.global_prefix_check)

    # --- LOGS UNE SEULE LIGNE ---
    def log_kick(self, guild, reason):
        owner = guild.owner if guild.owner else f"ID:{guild.owner_id}"
        # Print une seule ligne : [KICK-BL] Raison | Serveur: Nom (ID) | Owner: Nom
        print(f"{RED}[KICK-BL] {reason} | Serveur: {guild.name} ({guild.id}) | Owner: {owner}{RESET}")

    def log_attempt(self, user, command_name, cmd_type):
        # Print une seule ligne : [ALERTE-BL] Type | User: Nom (ID) | Commande: nom
        print(f"{RED}[ALERTE-BL] {cmd_type} | User: {user} ({user.id}) | Commande: {command_name}{RESET}")

    # --- SURVEILLANCE ACTIVE (20 SEC) ---
    @tasks.loop(seconds=20)
    async def security_scan(self):
        if not self.bot.is_ready(): return

        data = get_blacklist_data()
        b_users = [int(u['id']) for u in data.get("users", [])]
        b_servs = [int(s['id']) for s in data.get("servers", [])]

        for guild in self.bot.guilds:
            reason = None
            if guild.id in b_servs: reason = "Serveur black-list"
            elif guild.owner_id in b_users: reason = "Owner black-list"

            if reason:
                self.log_kick(guild, reason)
                try:
                    await guild.owner.send(f"🚫 **Sécurité** : Le bot a quitté votre serveur (Raison: {reason}).")
                except: pass
                await guild.leave()

    @security_scan.before_loop
    async def before_scan(self):
        await self.bot.wait_until_ready()

    # --- CHECK PREFIXES ---
    async def global_prefix_check(self, ctx):
        data = get_blacklist_data()
        b_users = [int(u['id']) for u in data.get("users", [])]
        
        if ctx.author.id in b_users:
            self.log_attempt(ctx.author, ctx.command.name if ctx.command else "Inconnue", "Prefix")
            await ctx.send(f"🚫 **{ctx.author.name}**, vous êtes blacklisté.", delete_after=5)
            return False
        return True

    # --- CHECK SLASH ---
    async def master_interaction_check(self, interaction: discord.Interaction) -> bool:
        uid = interaction.user.id
        data = get_blacklist_data()
        b_users = [int(u['id']) for u in data.get("users", [])]
        b_servs = [int(s['id']) for s in data.get("servers", [])]

        if uid in b_users:
            self.log_attempt(interaction.user, interaction.command.name if interaction.command else "Slash", "Slash")
            if not interaction.response.is_done():
                await interaction.response.send_message("🚫 Accès refusé : Blacklist.", ephemeral=True)
            return False

        if interaction.guild:
            reason = None
            if interaction.guild_id in b_servs: reason = "Serveur black-list"
            elif interaction.guild.owner_id in b_users: reason = "Owner black-list"

            if reason:
                self.log_kick(interaction.guild, reason)
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"🚫 Sécurité : {reason}.", ephemeral=True)
                await interaction.guild.leave()
                return False
        return True

async def setup(bot: commands.Bot):
    if bot.get_cog("BlacklistCog"):
        await bot.remove_cog("BlacklistCog")
    await bot.add_cog(BlacklistCog(bot))