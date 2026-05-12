"""Cog Modération — exemple Synkrone"""
import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Aucune raison"):
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} a été banni. Raison : {reason}")

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Aucune raison"):
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} a été expulsé. Raison : {reason}")

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, amount: int = 10):
        if amount < 1 or amount > 100:
            await ctx.send("Montant entre 1 et 100.")
            return
        deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"{len(deleted) - 1} messages supprimés.")
        await msg.delete(delay=3)

    @commands.command(name="slowmode")
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int = 0):
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Mode lent réglé à {seconds}s.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
