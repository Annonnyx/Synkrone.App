import discord
from discord.ext import commands
from discord import ui
import io
import json
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# ==============================================================================
# --------------------------- GESTIONNAIRE DE DONNÉES --------------------------
# ==============================================================================

class LeaveDataManager:
    def __init__(self):
        self.base_path = Path(__file__).parent / "data_leave"
        self.assets_path = Path(__file__).parent / "assets"
        self.default_font = self.assets_path / "arial.ttf"
        self.help_json = self.assets_path / "aide_aurevoir.json"
        if not self.base_path.exists(): self.base_path.mkdir(parents=True)

    def get_guild_folder(self, guild_id: int) -> Path:
        folder = self.base_path / str(guild_id)
        if not folder.exists(): folder.mkdir(parents=True)
        return folder

    def get_default_config(self):
        return {
            "enabled": False, 
            "channel_id": None,
            "is_private": True,
            "embed_title": "Départ de {user}",
            "embed_description": "Triste de te voir partir...",
            "content_message": "{user.mention} nous a quitté.\nNous sommes désormais {guild.count}."
        }

    def get_config(self, guild_id: int) -> dict:
        folder = self.get_guild_folder(guild_id)
        config_file = folder / "config.json"
        if not config_file.exists(): return self.get_default_config()
        with open(config_file, 'r', encoding='utf-8') as f:
            return {**self.get_default_config(), **json.load(f)}

    def save_config(self, guild_id: int, data: dict):
        folder = self.get_guild_folder(guild_id)
        with open(folder / "config.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

# ==============================================================================
# --------------------------- MODALS -------------------------------------------
# ==============================================================================

class LeaveChannelModal(ui.Modal, title="📍 Salon de Départ"):
    id_input = ui.TextInput(label="ID du Salon", placeholder="Collez l'ID ici...", min_length=15, max_length=25)
    def __init__(self, cog, view):
        super().__init__()
        self.cog, self.view = cog, view

    async def on_submit(self, it: discord.Interaction):
        try:
            conf = self.cog.data_manager.get_config(it.guild.id)
            conf['channel_id'] = int(self.id_input.value)
            self.cog.data_manager.save_config(it.guild.id, conf)
            await self.view.refresh(it)
        except:
            await it.response.send_message("❌ ID invalide.", ephemeral=True)

class LeaveTextModal(ui.Modal, title="📝 Textes de Départ"):
    t = ui.TextInput(label="Titre Embed", max_length=250)
    d = ui.TextInput(label="Description Embed", style=discord.TextStyle.paragraph)
    m = ui.TextInput(label="Message Hors Embed", style=discord.TextStyle.paragraph)
    
    def __init__(self, cog, view):
        super().__init__()
        self.cog, self.view = cog, view
        conf = self.cog.data_manager.get_config(view.guild_id)
        self.t.default, self.d.default, self.m.default = conf['embed_title'], conf['embed_description'], conf['content_message']

    async def on_submit(self, it: discord.Interaction):
        conf = self.cog.data_manager.get_config(self.view.guild_id)
        conf.update({"embed_title": self.t.value, "embed_description": self.d.value, "content_message": self.m.value})
        self.cog.data_manager.save_config(self.view.guild_id, conf)
        await self.view.refresh(it)

# ==============================================================================
# --------------------------- VIEW CONFIGURATION -------------------------------
# ==============================================================================

class LeaveView(ui.View):
    def __init__(self, cog, guild_id, user_preview):
        super().__init__(timeout=600)
        self.cog, self.guild_id, self.user_preview = cog, guild_id, user_preview
        self.sync_buttons()

    def sync_buttons(self):
        conf = self.cog.data_manager.get_config(self.guild_id)
        self.toggle_btn.emoji = "🟢" if conf['enabled'] else "🔴"
        self.visibility_btn.emoji = "🔒" if conf.get('is_private', True) else "🔓"
        
        bg_exists = (self.cog.data_manager.get_guild_folder(self.guild_id) / "background.png").exists()
        is_default = (conf == self.cog.data_manager.get_default_config()) and not bg_exists
        self.reset_btn.disabled = is_default

    async def refresh(self, it: discord.Interaction):
        if not it.response.is_done():
            await it.response.defer()
            
        self.sync_buttons()
        img = await self.cog.create_leave_image(self.user_preview, self.guild_id)
        
        conf = self.cog.data_manager.get_config(self.guild_id)
        chan = f"<#{conf['channel_id']}>" if conf['channel_id'] else "❌"
        vis = "🔒 Privé" if conf.get('is_private', True) else "🔓 Public (Lecture seule)"
        
        desc = f"📍 **Salon :** {chan}\n👁️ **Visibilité :** {vis}\n\n**Titre :** {self.cog.parse(conf['embed_title'], self.user_preview)}\n**Desc :** {self.cog.parse(conf['embed_description'], self.user_preview)}\n**Msg :** {self.cog.parse(conf['content_message'], self.user_preview)}"
        
        if config_manager:
            embed = config_manager.get_formatted_embed(it.guild, self.user_preview, self.cog.bot, "⚙️ Config Au Revoir", desc, it.guild.id)
        else:
            embed = discord.Embed(title="⚙️ Config Au Revoir", description=desc, color=0xe74c3c)
        
        embed.set_image(url="attachment://preview.png")
        file = discord.File(img, "preview.png")
        
        await it.edit_original_response(embed=embed, attachments=[file], view=self)

    @ui.button(style=discord.ButtonStyle.primary, row=0)
    async def toggle_btn(self, it: discord.Interaction, btn: ui.Button):
        conf = self.cog.data_manager.get_config(self.guild_id)
        conf['enabled'] = not conf['enabled']
        
        # Si on active et qu'aucun salon n'existe, on le crée avec le nouveau nom
        if conf['enabled'] and not conf['channel_id']:
            overwrites = {
                it.guild.default_role: discord.PermissionOverwrite(
                    view_channel=False, 
                    send_messages=False, 
                    create_public_threads=False,
                    create_private_threads=False,
                    send_messages_in_threads=False
                ),
                it.guild.me: discord.PermissionOverwrite(
                    view_channel=True, 
                    send_messages=True, 
                    attach_files=True
                )
            }
            try:
                # MISE À JOUR DU NOM ICI
                c = await it.guild.create_text_channel("🌙│𝑨𝒖-𝒓𝒆𝒗𝒐𝒊𝒓", overwrites=overwrites)
                conf['channel_id'] = c.id
                conf['is_private'] = True
            except: 
                pass
        
        self.cog.data_manager.save_config(self.guild_id, conf)
        await self.refresh(it)

    @ui.button(style=discord.ButtonStyle.secondary, row=0)
    async def visibility_btn(self, it: discord.Interaction, btn: ui.Button):
        conf = self.cog.data_manager.get_config(self.guild_id)
        conf['is_private'] = not conf.get('is_private', True)
        self.cog.data_manager.save_config(self.guild_id, conf)
        
        if conf['channel_id']:
            channel = it.guild.get_channel(conf['channel_id'])
            if channel:
                if conf['is_private']:
                    # Mode Privé : On cache tout
                    await channel.set_permissions(it.guild.default_role, view_channel=False)
                else:
                    # Mode Public : On montre mais on verrouille TOUT le reste
                    await channel.set_permissions(it.guild.default_role, 
                        view_channel=True, 
                        send_messages=False, 
                        create_public_threads=False,
                        create_private_threads=False,
                        send_messages_in_threads=False,
                        add_reactions=False # Optionnel : empêche aussi les réactions
                    )
        
        await self.refresh(it)

    @ui.button(emoji="❓", style=discord.ButtonStyle.secondary, row=0)
    async def help_btn(self, it: discord.Interaction, btn: ui.Button):
        path = self.cog.data_manager.help_json
        if not path.exists(): return await it.response.send_message("❌ JSON manquant.", ephemeral=True)
        with open(path, 'r', encoding='utf-8') as f: data = json.load(f)['help_embed']
        if config_manager: 
            embed = config_manager.get_formatted_embed(it.guild, it.user, self.cog.bot, data['title'], data['description'], it.guild.id)
        else: 
            embed = discord.Embed(title=data['title'], description=data['description'], color=data['color'])
        for f in data['fields']: embed.add_field(name=f['name'], value=f['value'], inline=False)
        await it.response.send_message(embed=embed, ephemeral=True)

    @ui.button(emoji="♻️", style=discord.ButtonStyle.danger, row=0)
    async def reset_btn(self, it: discord.Interaction, btn: ui.Button):
        self.cog.data_manager.save_config(self.guild_id, self.cog.data_manager.get_default_config())
        bg = self.cog.data_manager.get_guild_folder(self.guild_id) / "background.png"
        if bg.exists(): bg.unlink()
        await self.refresh(it)

    @ui.button(emoji="📝", style=discord.ButtonStyle.secondary, row=1)
    async def text_btn(self, it: discord.Interaction, btn: ui.Button):
        await it.response.send_modal(LeaveTextModal(self.cog, self))

    @ui.button(emoji="#️⃣", style=discord.ButtonStyle.secondary, row=1)
    async def channel_btn(self, it: discord.Interaction, btn: ui.Button):
        await it.response.send_modal(LeaveChannelModal(self.cog, self))

    @ui.button(emoji="🖼️", style=discord.ButtonStyle.secondary, row=1)
    async def bg_btn(self, it: discord.Interaction, btn: ui.Button):
        await it.response.send_message("📤 Envoyez l'image (PNG/JPG).", ephemeral=True)
        def check(m): return m.author.id == it.user.id and m.attachments
        try:
            msg = await self.cog.bot.wait_for('message', check=check, timeout=60)
            await msg.attachments[0].save(self.cog.data_manager.get_guild_folder(self.guild_id) / "background.png")
            try: await msg.delete()
            except: pass
            await self.refresh(it)
        except: pass

# ==============================================================================
# ---------------------------------- COG ---------------------------------------
# ==============================================================================

class AuRevoir(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = LeaveDataManager()

    async def create_leave_image(self, member, g_id):
        color = (231, 76, 60) # Rouge par défaut
        if config_manager:
            e = config_manager.get_formatted_embed(member.guild, member, self.bot, "t", "d", member.guild.id)
            if e.color: color = (e.color.r, e.color.g, e.color.b)

        bg_p = self.data_manager.get_guild_folder(g_id) / "background.png"
        W, H = 800, 300
        if bg_p.exists():
            image = ImageOps.fit(Image.open(bg_p).convert("RGBA"), (W, H), method=Image.Resampling.LANCZOS)
        else:
            image = Image.new('RGB', (W, H), color=(44, 47, 51))
            image = image.convert("RGBA")

        async with aiohttp.ClientSession() as s:
            async with s.get(str(member.display_avatar.url)) as r: av_d = await r.read()
        av = ImageOps.fit(Image.open(io.BytesIO(av_d)).convert("RGBA"), (160,160))
        mask = Image.new('L', (160,160), 0)
        ImageDraw.Draw(mask).ellipse((0,0,160,160), fill=255)
        av.putalpha(mask)

        draw = ImageDraw.Draw(image)
        draw.ellipse((54, 64, 226, 236), fill=color) 
        image.paste(av, (60, 70), av)

        overlay = Image.new('RGBA', (W,H), (0,0,0,0))
        ImageDraw.Draw(overlay).rectangle([250, 80, 750, 220], fill=(0,0,0,200))
        image = Image.alpha_composite(image, overlay)
        
        draw = ImageDraw.Draw(image)
        try: font = ImageFont.truetype(str(self.data_manager.default_font), 45)
        except: font = ImageFont.load_default()
        draw.text((270, 100), "AU REVOIR", fill=(255,255,255), font=font)
        
        # Nom avec majuscule
        name_text = str(member.name)[:15].capitalize()
        draw.text((270, 160), name_text, fill=color, font=font)

        buf = io.BytesIO()
        image.save(buf, format='PNG')
        buf.seek(0)
        return buf

    def parse(self, text, member):
        m = {"{user}": member.name, "{user.mention}": member.mention, "{guild}": member.guild.name, "{guild.count}": str(member.guild.member_count)}
        for k, v in m.items(): text = text.replace(k, v)
        return text

    async def get_config_embed(self, guild, user):
        conf = self.data_manager.get_config(guild.id)
        chan = f"<#{conf['channel_id']}>" if conf['channel_id'] else "❌"
        vis = "🔒 Privé" if conf.get('is_private', True) else "🔓 Public"
        desc = f"📍 **Salon :** {chan}\n👁️ **Visibilité :** {vis}\n\n**Titre :** {self.parse(conf['embed_title'], user)}\n**Desc :** {self.parse(conf['embed_description'], user)}\n**Msg :** {self.parse(conf['content_message'], user)}"
        if config_manager:
            e = config_manager.get_formatted_embed(guild, user, self.bot, "⚙️ Config Au Revoir", desc, guild.id)
        else: e = discord.Embed(title="⚙️ Config Au Revoir", description=desc, color=0xe74c3c)
        e.set_image(url="attachment://preview.png")
        return e

    @commands.hybrid_command(name="aurevoir", description="Configure le système de départ des membres.")
    @commands.has_permissions(administrator=True)
    async def aurevoir(self, ctx):
        await ctx.defer()
        img = await self.create_leave_image(ctx.author, ctx.guild.id)
        embed = await self.get_config_embed(ctx.guild, ctx.author)
        await ctx.send(embed=embed, file=discord.File(img, "preview.png"), view=LeaveView(self, ctx.guild.id, ctx.author))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        conf = self.data_manager.get_config(member.guild.id)
        if not conf['enabled'] or not conf['channel_id']: return
        chan = member.guild.get_channel(conf['channel_id'])
        if chan:
            img = await self.create_leave_image(member, member.guild.id)
            title = self.parse(conf['embed_title'], member)
            desc = self.parse(conf['embed_description'], member)
            if config_manager:
                e = config_manager.get_formatted_embed(member.guild, member, self.bot, title, desc, member.guild.id)
            else: e = discord.Embed(title=title, description=desc, color=0xe74c3c)
            e.set_image(url="attachment://leave.png")
            await chan.send(content=self.parse(conf['content_message'], member), embed=e, file=discord.File(img, "leave.png"))

async def setup(bot): await bot.add_cog(AuRevoir(bot))