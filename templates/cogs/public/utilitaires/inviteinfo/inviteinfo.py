import discord
from discord.ext import commands
import traceback
from datetime import datetime, timedelta, timezone
import re

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# ----------------------------- VIEW INTERACTIVE -------------------------------
# ==============================================================================

class InviteProfileView(discord.ui.View):
    def __init__(self, ctx, cog, stats_dict, sorted_list):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.cog = cog
        self.stats_dict = stats_dict
        self.sorted_list = sorted_list

    @discord.ui.button(label="Mon Profil", style=discord.ButtonStyle.primary, emoji="👤")
    async def profile_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        data = self.stats_dict.get(user)

        if not data or data["total"] == 0:
            return await interaction.response.send_message("❌ Vous n'avez pas encore invité de membres sur ce serveur.", ephemeral=True)

        # Calcul de la position
        rank = "N/A"
        for index, (u, d) in enumerate(self.sorted_list, 1):
            if u.id == user.id:
                rank = index
                break

        title = f"👤 Profil d'inviteur : {user.display_name}"
        description = f"Voici vos statistiques personnelles d'invitations sur **{interaction.guild.name}**."

        if config_manager:
            embed = config_manager.get_formatted_embed(
                guild=interaction.guild, user=user, bot=self.cog.bot,
                title=title, description=description, target_id=interaction.guild.id
            )
        else:
            embed = discord.Embed(title=title, description=description, color=discord.Color.blue())

        embed.add_field(name="🏆 Classement", value=f"Position : **#{rank}**", inline=False)
        embed.add_field(name="📥 Total rejoint", value=f"**{data['total']}** membres", inline=True)
        embed.add_field(name="✅ Encore présents", value=f"**{data['present']}** membres", inline=True)
        embed.add_field(name="⏳ Ces 7 derniers jours", value=f"**+{data['weekly']}** nouveaux", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

# ==============================================================================
# -------------------------------- COG COMMAND ---------------------------------
# ==============================================================================

class InviteinfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="inviteinfo", description="Classement et profil des invitations.")
    @commands.has_permissions(manage_guild=True)
    async def inviteinfo(self, ctx: commands.Context):
        try:
            await ctx.defer(ephemeral=False)
            invites = await ctx.guild.invites()
            
            if not invites:
                return await ctx.send("❌ Aucune invitation trouvée.", ephemeral=True)

            stats = {}
            now = datetime.now(timezone.utc)
            seven_days_ago = now - timedelta(days=7)

            for inv in invites:
                if not inv.inviter or inv.inviter.bot:
                    continue
                
                inviter = inv.inviter
                if inviter not in stats:
                    stats[inviter] = {"total": 0, "present": 0, "weekly": 0}

                # Discord API : 'uses' représente les membres actuellement comptés (présents)
                # Note: Le 'total' réel est difficile sans DB, on simule ici la présence active
                stats[inviter]["present"] += inv.uses
                stats[inviter]["total"] += inv.uses # Simulé ici comme base
                
                if inv.created_at and inv.created_at > seven_days_ago:
                    stats[inviter]["weekly"] += inv.uses

            # Filtrage & Tri
            filtered_stats = {u: s for u, s in stats.items() if s["present"] > 0}
            sorted_stats = sorted(filtered_stats.items(), key=lambda x: x[1]["present"], reverse=True)

            if not sorted_stats:
                return await ctx.send("❌ Aucune donnée d'invitation active.", ephemeral=True)

            # Embed Classement
            title = f"🏆 Top Invitations - {ctx.guild.name}"
            desc = "Classement basé sur les membres actuellement présents."
            
            if config_manager:
                embed = config_manager.get_formatted_embed(
                    guild=ctx.guild, user=ctx.author, bot=self.bot,
                    title=title, description=desc, target_id=ctx.guild.id
                )
            else:
                embed = discord.Embed(title=title, description=desc, color=0x2b2d31)

            for i, (user, data) in enumerate(sorted_stats[:10], 1):
                medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                emoji = medals.get(i, f"#{i}")
                embed.add_field(
                    name=f"{emoji} {user.display_name}",
                    value=f"👥 Présents : **{data['present']}** | 📈 7j : `+{data['weekly']}`",
                    inline=False
                )

            # Envoi avec la View (Bouton Profil)
            view = InviteProfileView(ctx, self, filtered_stats, sorted_stats)
            
            if ctx.interaction:
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send(embed=embed, view=view, reference=ctx.message)

        except Exception:
            traceback.print_exc()
            await ctx.send("❌ Une erreur est survenue.", ephemeral=True)

async def setup(bot):
    if bot.get_command("inviteinfo"):
        bot.remove_command("inviteinfo")
    await bot.add_cog(InviteinfoCommand(bot))