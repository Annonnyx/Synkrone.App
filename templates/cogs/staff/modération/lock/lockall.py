import discord
from discord.ext import commands
from pathlib import Path
import json
import asyncio
import random

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class LockAllCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_path = Path(__file__).parent / "data"
        self.data_path.mkdir(parents=True, exist_ok=True)

    @commands.hybrid_command(name="lockall", description="🚨 Verrouillage global du serveur.")
    @commands.has_permissions(administrator=True)
    async def lockall(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        
        file_path = self.data_path / f"{ctx.guild.id}.json"
        db = json.load(open(file_path, 'r', encoding='utf-8')) if file_path.exists() else {}
        target = ctx.guild.default_role
        
        channels = [c for c in ctx.guild.channels if isinstance(c, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))]
        total = len(channels)
        count = 0

        funny_messages = [
            "🔒 Fermeture des portes à double tour...",
            "🧱 On empile les briques devant les salons...",
            "🤫 Chut ! Tout le monde doit dormir maintenant...",
            "⛓️ On sort les chaînes et les cadenas...",
            "👮 Patrouille de sécurité en cours...",
            "🛠️ Installation des barreaux aux fenêtres..."
        ]

        progress_msg = await ctx.channel.send("🚀 **Initialisation du Lockdown...**")

        # Notification publique dans les salons
        if config_manager:
            lock_embed = config_manager.get_formatted_embed(
                guild=ctx.guild, user=ctx.author, bot=self.bot,
                title="🚨 Maintenance du Serveur",
                description="Le serveur est temporairement verrouillé. L'écriture est désactivée.",
                target_id=ctx.guild.id
            )
            lock_embed.color = 0xE74C3C
        else:
            lock_embed = discord.Embed(title="🚨 Maintenance", description="Écriture désactivée.", color=discord.Color.red())

        for channel in channels:
            cid = str(channel.id)
            if cid in db: continue
            
            try:
                # Capture pour préserver la synchro (view_channel)
                ov = channel.overwrites_for(target)
                db[cid] = {
                    "send_messages": ov.send_messages,
                    "add_reactions": ov.add_reactions,
                    "connect": ov.connect,
                    "speak": ov.speak,
                    "view_channel": ov.view_channel
                }

                if isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
                    await channel.set_permissions(target, send_messages=False, add_reactions=False, view_channel=ov.view_channel)
                    await channel.send(embed=lock_embed)
                elif isinstance(channel, discord.VoiceChannel):
                    await channel.set_permissions(target, connect=False, view_channel=ov.view_channel)
                
                count += 1
                
                if count % 2 == 0 or count == total:
                    status = random.choice(funny_messages)
                    percentage = int((count / total) * 10)
                    bar = "▰" * percentage + "▱" * (10 - percentage)
                    await progress_msg.edit(content=f"{status}\n`{bar}` **{count}/{total}**")
                
                await asyncio.sleep(0.4)
            except:
                continue

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4)

        if config_manager:
            final_embed = config_manager.get_formatted_embed(
                guild=ctx.guild, user=ctx.author, bot=self.bot,
                title="✅ Opération Terminée",
                description=f"Le serveur est désormais sécurisé.\n\n🔹 **{count}** salons verrouillés.\n🔹 Visibilité d'origine préservée.",
                target_id=ctx.guild.id
            )
            final_embed.color = 0x2ECC71
            await progress_msg.edit(content=None, embed=final_embed)
        else:
            await progress_msg.edit(content=f"✅ **Lockdown terminé !** {count} salons sécurisés.")

async def setup(bot): await bot.add_cog(LockAllCommand(bot))