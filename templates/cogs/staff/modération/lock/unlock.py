import discord
from discord.ext import commands
from pathlib import Path
import json

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class Unlock(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Chemin vers le dossier data partagé avec lock.py
        self.data_path = Path(__file__).parent / "data"

    @commands.hybrid_command(name="unlock", description="🔓 Déverrouille le salon actuel (si verrouillé par le bot).")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        
        file_path = self.data_path / f"{ctx.guild.id}.json"
        
        # 1. VÉRIFICATION DE SÉCURITÉ
        if not file_path.exists():
            return await ctx.send("❌ Aucune donnée de lock trouvée pour ce serveur.", ephemeral=True)

        with open(file_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        cid = str(ctx.channel.id)

        # On ne déverrouille QUE si le salon est dans le JSON
        if cid not in db:
            return await ctx.send(
                "❌ **Action annulée** : Ce salon n'a pas été verrouillé par le bot.\n"
                "Ceci évite de modifier accidentellement vos salons staff ou privés.", 
                ephemeral=True
            )

        # 2. RÉCUPÉRATION ET RESTAURATION
        perms = db[cid]
        target = ctx.guild.default_role
        
        # On recrée l'objet de permissions exact (incluant les Nones pour la synchro)
        new_ov = discord.PermissionOverwrite(
            send_messages=perms.get("send_messages"),
            add_reactions=perms.get("add_reactions"),
            connect=perms.get("connect"),
            speak=perms.get("speak"),
            view_channel=perms.get("view_channel")
        )

        # Application de l'overwrite complet
        await ctx.channel.set_permissions(target, overwrite=new_ov)

        # 3. NETTOYAGE DU JSON
        del db[cid]
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4)

        # 4. ENVOI DE L'EMBED
        rank = "Owner" if ctx.author.id == ctx.guild.owner_id else "Administrateur" if ctx.author.guild_permissions.administrator else "Modérateur"

        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=ctx.guild, user=ctx.author, bot=self.bot,
                title="🔓 Salon Déverrouillé",
                description=f"Le salon {ctx.channel.mention} a été restauré avec succès.",
                target_id=ctx.guild.id
            )
            embed.add_field(name="Autorité", value=rank)
            embed.color = 0x2ECC71
        else:
            embed = discord.Embed(
                title="🔓 Salon Déverrouillé", 
                description=f"Le salon a été rouvert par {ctx.author.mention}.", 
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Rang : {rank}")

        await ctx.channel.send(embed=embed)
        # Message éphémère de confirmation supprimé comme demandé précédemment.

async def setup(bot):
    await bot.add_cog(Unlock(bot))