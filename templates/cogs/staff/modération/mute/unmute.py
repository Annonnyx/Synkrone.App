import discord
from discord.ext import commands

class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = None):
        """
        Démute un utilisateur : retire le rôle mute global et le retire des fichiers JSON de mute, même si le rôle n'existe pas.
        """
        import json
        from pathlib import Path

        folder = Path(__file__).parent / "data"
        file_global = folder / f"{ctx.guild.id}_global.json"
        file_local = folder / f"{ctx.guild.id}.json"
        found = False
        info = None
        # Recherche dans le global
        if file_global.exists():
            try:
                dg = json.loads(file_global.read_text(encoding="utf-8"))
                if str(member.id) in dg:
                    info = dg.pop(str(member.id))
                    file_global.write_text(json.dumps(dg, indent=4), encoding="utf-8")
                    found = True
            except Exception:
                pass
        # Recherche dans le local si pas trouvé
        if not found and file_local.exists():
            try:
                dl = json.loads(file_local.read_text(encoding="utf-8"))
                if str(member.id) in dl:
                    info = dl.pop(str(member.id))
                    file_local.write_text(json.dumps(dl, indent=4), encoding="utf-8")
                    found = True
            except Exception:
                pass

        # On retire le rôle si présent
        mute_role = discord.utils.get(ctx.guild.roles, name="🧛│𝐴𝐶𝑀𝑈𝑇𝐸") or discord.utils.get(ctx.guild.roles, name="🤫│𝑴𝒖𝒆𝒕")
        if mute_role and mute_role in member.roles:
            try:
                await member.remove_roles(mute_role, reason=reason or "Unmute par commande")
            except Exception:
                pass

        if found:
            await ctx.send(f"🔊 {member.mention} a été démute et retiré de la liste des muets.")
        else:
            await ctx.send(f"❌ {member.mention} n'est pas dans la liste des muets (aucune sanction trouvée dans la data).")

async def setup(bot):
    await bot.add_cog(Unmute(bot))
