import discord
from discord.ext import commands, tasks
import json
from pathlib import Path

# Harmonisation du chemin racine
ROOT = Path(__file__).resolve().parents[3]

class AttribRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.attrib_roles_loop.start()

    def cog_unload(self):
        self.attrib_roles_loop.cancel()

    @tasks.loop(minutes=2)
    async def attrib_roles_loop(self):
        for guild in self.bot.guilds:
            lvl_path = ROOT / "data" / "pack" / "statistiques" / str(guild.id) / "lvl.json"
            if not lvl_path.exists():
                continue
            with open(lvl_path, encoding="utf-8") as f:
                lvls = json.load(f)
            lvls.sort(key=lambda x: int(x.get("niveau", 0)) if str(x.get("niveau", "")).isdigit() else 9999)
            for member in guild.members:
                if member.bot:
                    continue
                user_stats_path = ROOT / "data" / "pack" / "statistiques" / str(guild.id) / f"{member.id}.json"
                if not user_stats_path.exists():
                    continue
                with open(user_stats_path, encoding="utf-8") as f:
                    stats = json.load(f)
                user_level = int(stats.get("level", 1))
                roles_to_add = []
                roles_info = []  # Pour stocker (role, palier_lvl) pour notification
                for palier in lvls:
                    palier_lvl = int(palier.get("niveau", 0)) if str(palier.get("niveau", "")).isdigit() else 0
                    role_id = palier.get("role_id")
                    if role_id and user_level >= palier_lvl:
                        role = guild.get_role(int(role_id))
                        if role and role not in member.roles:
                            roles_to_add.append(role)
                            roles_info.append((role, palier_lvl))

                if roles_to_add:
                    try:
                        await member.add_roles(*roles_to_add, reason="Attribution automatique des rôles de niveau")
                        # Envoi d'un MP pour chaque rôle ajouté
                        for role, palier_lvl in roles_info:
                            try:
                                await member.send(f"Vous avez reçu le rôle **{role.name}** sur le serveur **{guild.name}** pour avoir atteint le niveau **{palier_lvl}** !")
                            except Exception:
                                pass  # Ignore si l'utilisateur a les MP fermés
                    except Exception as e:
                        if isinstance(e, discord.Forbidden) or (hasattr(e, 'code') and getattr(e, 'code', None) == 50013):
                            print(f"[AttribRoles] Impossible d'attribuer le rôle '{[role.name for role in roles_to_add]}" \
                                  f"' à {member.display_name} sur le serveur '{guild.name}' : Permissions insuffisantes.\n"
                                  f"Le bot ne peut pas donner un rôle égal ou supérieur à son propre rôle Discord. (403 Forbidden)")
                        else:
                            print(f"[AttribRoles] Erreur inattendue lors de l'attribution d'un rôle à {member.display_name} sur '{guild.name}' : {e}")
                        # Si erreur de permission, prévenir l'owner du serveur
                        if isinstance(e, discord.Forbidden) or (hasattr(e, 'code') and getattr(e, 'code', None) == 50013):
                            owner = getattr(guild, 'owner', None)
                            for role, palier_lvl in roles_info:
                                if owner:
                                    try:
                                        await owner.send(
                                            f"{member.mention} du serveur **{guild.name}** est passé niveau **{palier_lvl}**.\n"
                                            f"J'ai voulu lui attribuer le rôle `{role.mention}` mais je n'ai pas la permission (je ne peux pas donner de rôle égal ou supérieur au mien)."
                                        )
                                    except Exception:
                                        pass

async def setup(bot):
    # Sécurité anti-crash : retire le Cog s'il est déjà en mémoire avant de le recharger
    if bot.get_cog("AttribRoles"):
        await bot.remove_cog("AttribRoles")
        
    await bot.add_cog(AttribRoles(bot))