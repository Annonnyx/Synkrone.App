import discord
from discord import Member, Guild


def get_profile_embed(user: Member, guild: Guild = None) -> discord.Embed:
    """Retourne un embed Discord avec le maximum d'informations sur un utilisateur."""
    embed = discord.Embed(
        title=f"Profil de {user.display_name}",
        color=user.color if hasattr(user, "color") else discord.Color.blue(),
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="Nom Discord", value=user.name, inline=True)
    embed.add_field(name="ID", value=user.id, inline=True)
    embed.add_field(name="Créé le", value=user.created_at.strftime("%d/%m/%Y"), inline=True)
    if hasattr(user, "joined_at") and user.joined_at:
        embed.add_field(
            name="A rejoint le serveur", value=user.joined_at.strftime("%d/%m/%Y"), inline=True
        )
    if guild:
        roles = [r.mention for r in user.roles if r.name != "@everyone"]
        embed.add_field(
            name="Rôles", value=", ".join(roles) if roles else "Aucun", inline=False
        )
        perms = []
        perms_obj = user.guild_permissions
        if perms_obj.administrator:
            perms.append("Administrateur")
        if perms_obj.manage_guild:
            perms.append("Gérer le serveur")
        if perms_obj.manage_roles:
            perms.append("Gérer les rôles")
        if perms_obj.kick_members:
            perms.append("Expulser des membres")
        if perms_obj.ban_members:
            perms.append("Bannir des membres")
        if perms:
            embed.add_field(name="Permissions clés", value=", ".join(perms), inline=False)
    if hasattr(user, "banner") and user.banner:
        embed.set_image(url=user.banner.url)
    return embed
