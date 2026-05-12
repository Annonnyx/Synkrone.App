import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone
import json
import os
import asyncio

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from .utils import config_manager
    HAS_MANAGER = True
except ImportError:
    try:
        from cogs.addons.embed_type.utils import config_manager
        HAS_MANAGER = True
    except ImportError:
        config_manager = None
        HAS_MANAGER = False

class RoleAuto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(self.base_dir, "data")
        
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

        self.categories = {
            "base": {
                "label": "👥 Configuration de Base",
                "roles": {
                    "bot": {"name": "🤖│𝑩𝒐𝒕𝒔", "color": 0x7289da, "desc": "Attribué aux bots (⚠️ ADMIN)", "admin": True},
                    "membre": {"name": "👤│𝑴𝒆𝒎𝒃𝒓𝒆𝒔", "color": 0x95a5a6, "desc": "Attribué aux humains", "admin": False}
                }
            },
            "ancienneté": {
                "label": "⏳ Modules d'Ancienneté",
                "roles": {
                    "1_mois": {"name": "⏳│𝟏 𝑴𝒐𝒊𝒔", "color": 0x3498db, "days": 30, "desc": "30 jours"},
                    "3_mois": {"name": "⏳│𝟑 𝑴𝒐𝒊𝒔", "color": 0x2ecc71, "days": 90, "desc": "90 jours"},
                    "6_mois": {"name": "⏳│𝟔 𝑴𝒐𝒊𝒔", "color": 0x9b59b6, "days": 180, "desc": "180 jours"},
                    "1_an": {"name": "🏆│𝟏 𝑨𝒏", "color": 0xf1c40f, "days": 365, "desc": "1 an"},
                    "2_ans": {"name": "🏆│𝟐 𝑨𝒏𝒔", "color": 0x1abc9c, "days": 730, "desc": "2 ans"},
                    "3_ans": {"name": "👑│𝟑 𝑨𝒏𝒔+", "color": 0xe91e63, "days": 1095, "desc": "3 ans+"}
                }
            }
        }
        self.server_data = {}
        self.check_all_roles.start()

    def get_or_load_data(self, gid):
        if gid not in self.server_data:
            path = os.path.join(self.data_path, f"{gid}.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f: self.server_data[gid] = json.load(f)
            else: self.server_data[gid] = {"enabled_features": [], "roles": {}}
        return self.server_data[gid]

    async def apply_roles_to_all(self, guild):
        data = self.get_or_load_data(str(guild.id))
        report = {} 
        for member in guild.members:
            added = await self.process_member_roles(member, data)
            for r in added:
                if r.id not in report: report[r.id] = []
                report[r.id].append(member.mention)
        return report

    async def process_member_roles(self, member, data):
        if not member.bot and member.guild_permissions.administrator: return []
        added_roles, removed_roles = [], []
        now = datetime.now(timezone.utc)
        feats = data.get("enabled_features", [])
        
        if "base" in feats:
            for r_key in ["bot", "membre"]:
                r_id = data["roles"].get(r_key)
                role = member.guild.get_role(int(r_id)) if r_id else None
                if not role: continue
                if (r_key == "bot" and member.bot) or (r_key == "membre" and not member.bot):
                    if role not in member.roles: added_roles.append(role)

        if "ancienneté" in feats and not member.bot:
            days = (now - member.joined_at).days
            for r_key, r_info in self.categories["ancienneté"]["roles"].items():
                r_id = data["roles"].get(r_key)
                role = member.guild.get_role(int(r_id)) if r_id else None
                if role:
                    if days >= r_info["days"]:
                        if role not in member.roles: added_roles.append(role)
                    else:
                        if role in member.roles: removed_roles.append(role)

        try:
            if added_roles: await member.add_roles(*added_roles)
            if removed_roles: await member.remove_roles(*removed_roles)
        except: pass
        return added_roles

    async def ensure_category_roles(self, guild, cat_key):
        gid = str(guild.id)
        for r_key, r_info in self.categories[cat_key]["roles"].items():
            current_id = self.server_data[gid]["roles"].get(r_key)
            role = guild.get_role(int(current_id)) if current_id else None
            if not role:
                perms = discord.Permissions(administrator=True) if r_info.get("admin") else discord.Permissions.none()
                new_role = await guild.create_role(name=r_info["name"], color=discord.Color(r_info["color"]), hoist=True, permissions=perms)
                self.server_data[gid]["roles"][r_key] = str(new_role.id)
        
        ordered = []
        for ck in ["ancienneté", "base"]:
            for rk in self.categories[ck]["roles"].keys():
                rid = self.server_data[gid]["roles"].get(rk)
                r = guild.get_role(int(rid)) if rid else None
                if r:
                    if rk == "bot": ordered.insert(0, r)
                    else: ordered.append(r)
        
        ordered.reverse()
        positions = {role: idx + 1 for idx, role in enumerate(ordered)}
        try: await guild.edit_role_positions(positions=positions)
        except: pass

    @tasks.loop(minutes=30)
    async def check_all_roles(self):
        for guild in self.bot.guilds: await self.apply_roles_to_all(guild)

    @commands.hybrid_command(name="roleauto", description="Menu de configuration des rôles automatiques")
    @commands.has_permissions(administrator=True)
    async def roleauto(self, ctx: commands.Context):
        self.get_or_load_data(str(ctx.guild.id))
        await ctx.send(embed=self.create_embed(ctx), view=RoleAutoView(self, ctx.guild))

    def create_embed(self, ctx):
        gid = str(ctx.guild.id)
        data = self.server_data[gid]
        title = "👤│𝑹𝒐̂𝒍𝒆𝒔 𝑨𝒖𝒕𝒐𝒎𝒂𝒕𝒊𝒒𝒖𝒆𝒔"
        desc = (
            "Gestion de l'attribution automatique.\n\n"
            "💡 **Note :** Les rôles générés par défaut peuvent être **renommés** librement. "
            "Si vous configurez vos propres IDs, vous pouvez supprimer les rôles créés par le bot.\n"
        )
        
        if HAS_MANAGER and config_manager:
            embed = config_manager.get_formatted_embed(ctx.guild, ctx.author, self.bot, title, desc, ctx.guild.id)
        else:
            embed = discord.Embed(title=title, description=desc, color=0x2b2d31)

        for k, v in self.categories.items():
            status = "✅" if k in data["enabled_features"] else "❌"
            lines = [f"• <@&{data['roles'].get(rk)}> ➜ *{ri['desc']}*" if data['roles'].get(rk) else f"• `{ri['name']}`" for rk, ri in v["roles"].items()]
            embed.add_field(name=f"{v['label']} {status}", value="\n".join(lines), inline=False)
        return embed

class RoleAutoView(discord.ui.View):
    def __init__(self, cog, guild):
        super().__init__(timeout=None)
        self.cog, self.guild = cog, guild
        self.setup_components()

    def setup_components(self):
        self.clear_items()
        feats = self.cog.get_or_load_data(str(self.guild.id)).get("enabled_features", [])
        self.add_item(StateButton(label="Module Base", emoji="👥", style=discord.ButtonStyle.green if "base" in feats else discord.ButtonStyle.red, custom_id="toggle_base"))
        self.add_item(StateButton(label="Ancienneté", emoji="⏳", style=discord.ButtonStyle.green if "ancienneté" in feats else discord.ButtonStyle.red, custom_id="toggle_ancienneté"))
        self.add_item(RoleManualSelect(self.cog, self.guild))

    async def refresh(self, interaction):
        self.setup_components()
        class FakeCtx:
            def __init__(self, i, bot): self.guild, self.author, self.bot = i.guild, i.user, bot
        await interaction.edit_original_response(embed=self.cog.create_embed(FakeCtx(interaction, self.cog.bot)), view=self)

class StateButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cog, guild, gid = self.view.cog, self.view.guild, str(self.view.guild.id)
        data = cog.server_data[gid]
        feat = "base" if self.custom_id == "toggle_base" else "ancienneté"
        
        if feat in data["enabled_features"]:
            data["enabled_features"].remove(feat)
            for r_key in cog.categories[feat]["roles"].keys():
                r_id = data["roles"].pop(r_key, None)
                if r_id:
                    role = guild.get_role(int(r_id))
                    if role: await role.delete()
            await interaction.followup.send(f"✅ Module `{feat}` désactivé. Rôles supprimés.", ephemeral=True)
        else:
            data["enabled_features"].append(feat)
            status_msg = await interaction.followup.send(f"⏳ Activation et scan de `{feat}`...", ephemeral=True)
            await cog.ensure_category_roles(guild, feat)
            report = await cog.apply_roles_to_all(guild)
            
            if report:
                await self.send_report_embed(interaction, report, feat)
            
            await status_msg.edit(content=f"✅ Module `{feat}` configuré avec succès !")

        with open(os.path.join(cog.data_path, f"{gid}.json"), "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
        await self.view.refresh(interaction)

    async def send_report_embed(self, interaction, report, feat):
        embeds = []
        current_embed = discord.Embed(title=f"📈 Rapport d'attribution : {feat.capitalize()}", color=0x2ecc71)
        field_count = 0
        
        for rid, members in report.items():
            role = interaction.guild.get_role(int(rid))
            role_name = role.name if role else "Rôle Inconnu"
            member_list = "\n".join([f"- {m}" for m in members])
            
            if len(member_list) > 1024: member_list = member_list[:1020] + "..."

            current_embed.add_field(name=f"🏷️ {role_name}", value=member_list if members else "*Aucun membre*", inline=False)
            field_count += 1
            
            if field_count >= 5:
                embeds.append(current_embed)
                current_embed = discord.Embed(title=f"📈 Rapport d'attribution : {feat.capitalize()} (Suite)", color=0x2ecc71)
                field_count = 0
        
        if field_count > 0: embeds.append(current_embed)
        for emb in embeds: await interaction.followup.send(embed=emb, ephemeral=True)

class RoleManualSelect(discord.ui.Select):
    def __init__(self, cog, guild):
        self.cog, self.guild = cog, guild
        options = [discord.SelectOption(label=ri["name"].split("│")[-1], value=rk, emoji="🆔") for cat in cog.categories.values() for rk, ri in cat["roles"].items()]
        super().__init__(placeholder="🆔 Modifier l'ID d'un rôle", options=options[:25], row=2)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RoleEditModal(self.cog, self.guild, self.values[0], self.view))

class RoleEditModal(discord.ui.Modal, title="Lier un rôle existant"):
    rid = discord.ui.TextInput(label="ID Discord du rôle", placeholder="Collez l'ID ici...")
    def __init__(self, cog, guild, key, view): super().__init__(); self.cog, self.guild, self.key, self.parent_view = cog, guild, key, view
    async def on_submit(self, interaction: discord.Interaction):
        self.cog.server_data[str(self.guild.id)]["roles"][self.key] = self.rid.value
        with open(os.path.join(self.cog.data_path, f"{self.guild.id}.json"), "w", encoding="utf-8") as f: json.dump(self.cog.server_data[str(self.guild.id)], f, indent=4)
        await self.cog.apply_roles_to_all(self.guild)
        await interaction.response.send_message("✅ ID mis à jour et attribution lancée.", ephemeral=True)
        await self.parent_view.refresh(interaction)

async def setup(bot): await bot.add_cog(RoleAuto(bot))