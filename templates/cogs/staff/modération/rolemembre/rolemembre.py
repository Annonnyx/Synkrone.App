import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import time
import re
import traceback
from typing import Optional, List
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# --------------------------- GESTION PERSISTANCE ------------------------------
# ==============================================================================

class TempRoleManager:
    def __init__(self, folder_path="role_temp"):
        self.folder_path = Path(__file__).parent / folder_path
        if not self.folder_path.exists():
            self.folder_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, guild_id):
        return self.folder_path / f"{guild_id}.json"

    def load_data(self, guild_id):
        path = self._get_path(guild_id)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                try: return json.load(f)
                except: return []
        return []

    def save_temp_role(self, guild_id, member_id, role_id, end_time):
        data = self.load_data(guild_id)
        data.append({"member_id": member_id, "role_id": role_id, "end_time": end_time})
        with open(self._get_path(guild_id), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def remove_entry(self, guild_id, entry):
        data = self.load_data(guild_id)
        data = [d for d in data if not (d['member_id'] == entry['member_id'] and d['role_id'] == entry['role_id'])]
        with open(self._get_path(guild_id), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

# ==============================================================================
# --------------------------- INTERFACE INTERACTIVE ----------------------------
# ==============================================================================

class RoleModal(discord.ui.Modal, title="Configuration du Rôle"):
    role_id = discord.ui.TextInput(label="ID du Rôle", placeholder="Collez l'ID ici...", min_length=15, required=True)
    def __init__(self, view):
        super().__init__()
        self.view = view
    async def on_submit(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(int(self.role_id.value)) if self.role_id.value.isdigit() else None
        if not role: return await interaction.response.send_message("❌ Rôle introuvable.", ephemeral=True)
        self.view.selected_role = role
        await self.view.update_message(interaction)

class DurationModal(discord.ui.Modal, title="Définir la durée"):
    duration = discord.ui.TextInput(label="Durée", placeholder="Ex: 10s, 5m, 2h, 1d", min_length=2, required=True)
    def __init__(self, view):
        super().__init__()
        self.view = view
    async def on_submit(self, interaction: discord.Interaction):
        seconds = self.view.cog.parse_duration(self.duration.value)
        if not seconds: return await interaction.response.send_message("❌ Format invalide.", ephemeral=True)
        self.view.duration_str, self.view.duration_seconds = self.duration.value, seconds
        await self.view.update_message(interaction)

class RoleControlView(discord.ui.View):
    def __init__(self, ctx, cog):
        super().__init__(timeout=600)
        self.ctx, self.cog = ctx, cog
        self.action, self.target_type = "Ajouter", "Everyone"
        self.selected_role, self.selected_members = None, []
        self.duration_str, self.duration_seconds = "Permanent", None

    def get_base_embed(self, title, description):
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=self.ctx.guild, user=self.ctx.author, bot=self.cog.bot,
                title=title, description=description,
                target_id=self.ctx.guild.id if self.ctx.guild else None
            )
        return discord.Embed(title=title, description=description, color=0x2b2d31)

    def create_main_embed(self):
        embed = self.get_base_embed("🛠️ Programmation RoleMembre", "Configurez l'action groupée ci-dessous.")
        embed.add_field(name=f"{'➕' if self.action == 'Ajouter' else '➖'} Action", value=f"**{self.action}**", inline=True)
        embed.add_field(name=f"{'🌍' if self.target_type == 'Everyone' else '👥'} Cible", value=f"**{self.target_type}**", inline=True)
        embed.add_field(name="🆔 Rôle", value=self.selected_role.mention if self.selected_role else "❌ *Non défini*", inline=True)
        if self.target_type == "Utilisateurs":
            m_list = ", ".join([m.mention for m in self.selected_members]) if self.selected_members else "⏳ *En attente de saisie chat...*"
            embed.add_field(name="👥 Utilisateurs", value=m_list, inline=False)
        if self.action == "Ajouter":
            embed.add_field(name="⏳ Durée", value=f"**{self.duration_str}**", inline=True)
        return embed

    async def update_message(self, interaction: discord.Interaction):
        self.btn_members.disabled = (self.target_type == "Everyone")
        self.btn_temp.disabled = (self.action == "Retirer")
        await interaction.response.edit_message(embed=self.create_main_embed(), view=self)

    @discord.ui.select(options=[discord.SelectOption(label="Ajouter", value="Ajouter", emoji="➕"), discord.SelectOption(label="Retirer", value="Retirer", emoji="➖")], placeholder="🔧 Action...")
    async def select_action(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.action = select.values[0]
        await self.update_message(interaction)

    @discord.ui.select(options=[discord.SelectOption(label="Everyone", value="Everyone", emoji="🌍"), discord.SelectOption(label="Utilisateurs spécifiques", value="Utilisateurs", emoji="👥")], placeholder="👥 Cible...")
    async def select_target(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.target_type = select.values[0]
        await self.update_message(interaction)

    @discord.ui.button(label="Rôle (ID)", style=discord.ButtonStyle.secondary, emoji="🆔")
    async def btn_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RoleModal(self))

    @discord.ui.button(label="Saisir Membres", style=discord.ButtonStyle.secondary, emoji="💬", disabled=True)
    async def btn_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("👉 Envoyez les IDs/Mentions dans le chat.", ephemeral=True)
        def check(m): return m.author == self.ctx.author and m.channel == self.ctx.channel
        try:
            msg = await self.cog.bot.wait_for("message", check=check, timeout=60.0)
            ids = list(set(re.findall(r'\d{17,19}', msg.content)))
            self.selected_members = [self.ctx.guild.get_member(int(mid)) for mid in ids if self.ctx.guild.get_member(int(mid))]
            try: await msg.delete()
            except: pass
            await self.update_message(interaction)
        except asyncio.TimeoutError: pass

    @discord.ui.button(label="Temporaire", style=discord.ButtonStyle.secondary, emoji="⏳")
    async def btn_temp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DurationModal(self))

    @discord.ui.button(label="LANCER", style=discord.ButtonStyle.success, emoji="🚀", row=4)
    async def btn_execute(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_role: return await interaction.response.send_message("❌ Rôle manquant.", ephemeral=True)
        targets = [m for m in self.ctx.guild.members if not m.bot] if self.target_type == "Everyone" else self.selected_members
        if not targets: return await interaction.response.send_message("❌ Personne à traiter.", ephemeral=True)

        await interaction.response.defer()
        success, fail = 0, 0
        for m in targets:
            try:
                if self.action == "Ajouter":
                    await m.add_roles(self.selected_role)
                    if self.duration_seconds: self.cog.db.save_temp_role(self.ctx.guild.id, m.id, self.selected_role.id, time.time() + self.duration_seconds)
                else: await m.remove_roles(self.selected_role)
                success += 1
            except: fail += 1

        embed = self.get_base_embed("✅ Opération Terminée", f"Appliqué sur **{success}** membres.\n❌ Échecs : `{fail}`")
        if self.ctx.interaction: await self.ctx.interaction.followup.send(embed=embed)
        else: await self.ctx.send(embed=embed, reference=self.ctx.message)
        self.stop()

# ==============================================================================
# -------------------------------- COG PRINCIPAL -------------------------------
# ==============================================================================

class RoleMembre(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = TempRoleManager()
        self.check_temp_roles.start()

    def parse_duration(self, s: str):
        m = re.fullmatch(r"(\d+)([smhd])", s.lower())
        return int(m[1]) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[m[2]] if m else None

    @tasks.loop(minutes=30)
    async def check_temp_roles(self):
        now = time.time()
        for filename in os.listdir(self.db.folder_path):
            if not filename.endswith(".json"): continue
            gid = int(filename.split(".")[0])
            guild = self.bot.get_guild(gid)
            if not guild: continue
            for entry in self.db.load_data(gid):
                if now >= entry['end_time']:
                    m, r = guild.get_member(entry['member_id']), guild.get_role(entry['role_id'])
                    if m and r:
                        try: await m.remove_roles(r, reason="Expiration RoleMembre")
                        except: pass
                    self.db.remove_entry(gid, entry)

    @commands.hybrid_command(name="rolemembre", description="Gérer les rôles massivement.")
    @commands.has_permissions(manage_roles=True)
    async def rolemembre(self, ctx: commands.Context):
        try:
            await ctx.defer(ephemeral=False)
            view = RoleControlView(ctx, self)
            embed = view.create_main_embed()
            if ctx.interaction: await ctx.send(embed=embed, view=view)
            else: await ctx.send(embed=embed, view=view, reference=ctx.message, mention_author=True)
        except Exception:
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(RoleMembre(bot))