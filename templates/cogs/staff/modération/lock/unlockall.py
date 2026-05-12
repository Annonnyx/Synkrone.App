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

class UnlockAllCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_path = Path(__file__).parent / "data"

    @commands.hybrid_command(name="unlockall", description="🔓 Réouverture complète du serveur.")
    @commands.has_permissions(administrator=True)
    async def unlockall(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        
        file_path = self.data_path / f"{ctx.guild.id}.json"
        if not file_path.exists():
            return await ctx.send("❌ Aucune donnée de lockdown trouvée.", ephemeral=True)

        with open(file_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        total = len(db)
        count = 0
        target = ctx.guild.default_role
        
        funny_messages = [
            "🔑 On retrouve les clés au fond des poches...",
            "🔓 Déblocage des verrous en cours...",
            "🎈 C'est la fête, on rouvre tout !",
            "🧹 On retire les rubans de sécurité...",
            "⚡ Restauration de la parole pour tous...",
            "🔓 Les membres peuvent à nouveau s'exprimer !"
        ]

        progress_msg = await ctx.channel.send("🚀 **Lancement de la réouverture...**")

        if config_manager:
            unlock_embed = config_manager.get_formatted_embed(
                guild=ctx.guild, user=ctx.author, bot=self.bot,
                title="🔓 Fin de Maintenance",
                description="Le serveur est de nouveau accessible. Merci de votre patience !",
                target_id=ctx.guild.id
            )
            unlock_embed.color = 0x2ECC71
        else:
            unlock_embed = discord.Embed(title="🔓 Ouvert", description="Le serveur est rouvert.", color=discord.Color.green())

        for cid, perms in list(db.items()):
            channel = ctx.guild.get_channel(int(cid))
            if channel:
                try:
                    # Restauration exacte incluant les 'None' (Héritage/Synchro)
                    new_ov = discord.PermissionOverwrite(
                        send_messages=perms.get("send_messages"),
                        add_reactions=perms.get("add_reactions"),
                        connect=perms.get("connect"),
                        speak=perms.get("speak"),
                        view_channel=perms.get("view_channel")
                    )
                    await channel.set_permissions(target, overwrite=new_ov)
                    
                    if isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
                        await channel.send(embed=unlock_embed)
                    
                    count += 1
                    if count % 2 == 0 or count == total:
                        status = random.choice(funny_messages)
                        percentage = int((count / total) * 10)
                        bar = "▰" * percentage + "▱" * (10 - percentage)
                        await progress_msg.edit(content=f"{status}\n`{bar}` **{count}/{total}**")
                    
                    await asyncio.sleep(0.4)
                except: pass
            del db[cid]

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4)

        if config_manager:
            final_embed = config_manager.get_formatted_embed(
                guild=ctx.guild, user=ctx.author, bot=self.bot,
                title="✨ Serveur Restauré",
                description=f"La réouverture est terminée.\n\n🔹 **{count}** salons restaurés.\n🔹 Les permissions d'origine sont de retour.",
                target_id=ctx.guild.id
            )
            final_embed.color = 0x3498DB
            await progress_msg.edit(content=None, embed=final_embed)
        else:
            await progress_msg.edit(content=f"✅ **Réouverture terminée !** {count} salons restaurés.")

async def setup(bot): await bot.add_cog(UnlockAllCommand(bot))