import discord, json, asyncio, traceback
from discord.ext import commands
from discord import app_commands, ui
from pathlib import Path

# --- SYSTÈME D'IMPORT CONFIG_MANAGER ---
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# --- MODALS ---
class LimitModal(ui.Modal, title="Modifier la limite"):
    limit = ui.TextInput(label="Places (0 = illimité)", placeholder="Ex: 5", max_length=2)
    
    def __init__(self, channel, view):
        super().__init__()
        self.channel, self.view = channel, view

    async def on_submit(self, it: discord.Interaction):
        # 1. On dit à Discord qu'on a bien reçu la demande pour éviter le message d'erreur
        await it.response.defer(ephemeral=True)
        
        try:
            val = int(self.limit.value)
            if 0 <= val <= 99:
                # 2. On applique le changement sur le salon
                await self.channel.edit(user_limit=val)
                print(f"[DEBUG] Limite modifiée à {val} pour {self.channel.name}")
                
                # 3. On met à jour l'embed du panel MP
                # On utilise follow_up=True car on a déjà fait un defer()
                await self.view.update_panel(it, follow_up=True)
            else:
                await it.followup.send("❌ Le nombre doit être compris entre 0 et 99.", ephemeral=True)
        
        except ValueError:
            await it.followup.send("❌ Veuillez entrer un nombre valide.", ephemeral=True)
        except Exception as e:
            print(f"[ERROR] LimitModal Submit: {e}")

class BanModal(ui.Modal, title="Bannir par ID"):
    user_id = ui.TextInput(label="ID de l'utilisateur", placeholder="Collez l'ID ici...", min_length=15)
    def __init__(self, channel, view):
        super().__init__()
        self.channel, self.view = channel, view

    async def on_submit(self, it: discord.Interaction):
        guild = self.channel.guild # Sécurité NoneType MP
        try:
            target = guild.get_member(int(self.user_id.value))
            if not target:
                return await it.response.send_message("❌ Utilisateur introuvable sur le serveur.", ephemeral=True)
            
            await self.channel.set_permissions(target, connect=False, view_channel=False)
            if target in self.channel.members:
                await target.move_to(None)
            
            print(f"[DEBUG] {target.name} banni de {self.channel.name}")
            await it.response.send_message(f"✅ {target.display_name} banni.", ephemeral=True)
            await self.view.update_panel(it, follow_up=True)
        except Exception as e:
            print(f"[ERROR] BanModal: {e}")
            await it.response.send_message("❌ ID Invalide.", ephemeral=True)

# --- VIEW DU PANEL (ENVOYÉ EN MP) ---
class VoiceControlView(ui.View):
    def __init__(self, channel_id: int, bot: discord.Client):
        super().__init__(timeout=None)
        self.channel_id, self.bot = channel_id, bot

    async def update_panel(self, it: discord.Interaction, follow_up=False):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print(f"[ERROR] update_panel: Salon {self.channel_id} introuvable.")
            return

        guild = channel.guild
        ov = channel.overwrites_for(guild.default_role)
        
        vis = "✅ Visible" if ov.view_channel is not False else "❌ Masqué"
        acc = "✅ Ouvert" if ov.connect is not False else "🔒 Bloqué"
        lim = channel.user_limit if channel.user_limit > 0 else "∞ Illimitée"
        
        m_list = "\n".join([f"• {m.display_name}" for m in channel.members]) or "Aucun"
        bans = [f"• {obj.display_name}" for obj, ow in channel.overwrites.items() 
                if isinstance(obj, discord.Member) and ow.connect is False]
        banlist_str = "\n".join(bans) or "Aucun"

        embed = discord.Embed(title="🎧 Gestion de ton Vocal", color=0x2b2d31)
        embed.add_field(name="⚙️ Configuration", value=f"**Visibilité :** {vis}\n**Accès :** {acc}\n**Limite :** {lim}", inline=False)
        embed.add_field(name="👥 Membres", value=m_list, inline=True)
        embed.add_field(name="🚫 Banlist", value=banlist_str, inline=True)

        try:
            if follow_up:
                await it.edit_original_response(embed=embed, view=self)
            else:
                await it.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"[ERROR] update_panel edit: {e}")

    @ui.button(label="👁️ Visibilité", style=discord.ButtonStyle.secondary)
    async def toggle_vis(self, it: discord.Interaction, btn: ui.Button):
        chan = self.bot.get_channel(self.channel_id)
        if not chan: return
        everyone = chan.guild.default_role
        is_visible = chan.overwrites_for(everyone).view_channel
        # Si c'est None (neutre) ou True, on cache. Sinon on montre.
        await chan.set_permissions(everyone, view_channel=False if is_visible is not False else True)
        await self.update_panel(it)

    @ui.button(label="🔒 Accès", style=discord.ButtonStyle.secondary)
    async def toggle_lock(self, it: discord.Interaction, btn: ui.Button):
        chan = self.bot.get_channel(self.channel_id)
        if not chan: return
        everyone = chan.guild.default_role
        can_join = chan.overwrites_for(everyone).connect
        await chan.set_permissions(everyone, connect=False if can_join is not False else True)
        await self.update_panel(it)

    @ui.button(label="👥 Limite", style=discord.ButtonStyle.secondary)
    async def set_limit(self, it: discord.Interaction, btn: ui.Button):
        chan = self.bot.get_channel(self.channel_id)
        if not chan: return
        await it.response.send_modal(LimitModal(chan, self))

    @ui.button(label="🔨 Bannir ID", style=discord.ButtonStyle.danger)
    async def ban_id(self, it: discord.Interaction, btn: ui.Button):
        chan = self.bot.get_channel(self.channel_id)
        if not chan: return
        await it.response.send_modal(BanModal(chan, self))

# --- COG PRINCIPAL ---
class TemporaryVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = Path(__file__).parent / "data"
        self.data_path.mkdir(exist_ok=True)

    def get_db(self, gid):
        p = self.data_path / f"{gid}.json"
        if not p.exists(): p.write_text(json.dumps({"root_id": None, "actives": {}}))
        try:
            return json.loads(p.read_text())
        except Exception as e:
            print(f"[ERROR] get_db JSON corrompu: {e}")
            return {"root_id": None, "actives": {}}

    def save_db(self, gid, data):
        (self.data_path / f"{gid}.json").write_text(json.dumps(data, indent=4))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return
        db = self.get_db(member.guild.id)
        root_id = db.get("root_id")
        
        # 1. CRÉATION DU SALON
        if after.channel and after.channel.id == root_id:
            print(f"[DEBUG] {member.name} a rejoint le salon racine.")
            
            # Si déjà un salon actif, on le redirige
            if str(member.id) in db["actives"]:
                ex = member.guild.get_channel(db["actives"][str(member.id)])
                if ex:
                    print(f"[DEBUG] Redirection de {member.name} vers son salon existant.")
                    return await member.move_to(ex)

            try:
                ov = {
                    member.guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True),
                    member: discord.PermissionOverwrite(manage_channels=True, connect=True, view_channel=True, move_members=True, mute_members=True)
                }
                new = await member.guild.create_voice_channel(
                    name=f"🔊 {member.display_name}", 
                    category=after.channel.category, 
                    overwrites=ov
                )
                
                db["actives"][str(member.id)] = new.id
                self.save_db(member.guild.id, db)
                await member.move_to(new)
                print(f"[DEBUG] Salon temporaire créé: {new.name}")

                # Envoi du Panel
                embed = discord.Embed(title="🎧 Gestion de ton Vocal", color=0x2b2d31)
                embed.description = "Ton salon a été créé. Utilise ce panel pour le gérer."
                embed.add_field(name="⚙️ Configuration", value="**Visibilité :** ✅ Visible\n**Accès :** ✅ Ouvert\n**Limite :** ∞ Illimitée")
                try:
                    await member.send(embed=embed, view=VoiceControlView(new.id, self.bot))
                except:
                    print(f"[WARNING] Impossible d'envoyer le MP à {member.name}")
                
            except Exception as e:
                print(f"[ERROR] on_voice_state_update (Create): {e}")
                traceback.print_exc()

        # 2. SUPPRESSION DU SALON
        if before.channel:
            # On vérifie si c'est un salon actif dans la DB
            owner_id = next((k for k, v in db["actives"].items() if v == before.channel.id), None)
            if owner_id and len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                    print(f"[DEBUG] Salon vide supprimé: {before.channel.id}")
                    del db["actives"][owner_id]
                    self.save_db(member.guild.id, db)
                except Exception as e:
                    print(f"[ERROR] on_voice_state_update (Delete): {e}")

    @commands.hybrid_command(name="voice", description="Gérer le salon racine vocal.")
    @commands.has_permissions(manage_channels=True)
    async def voice_setup(self, ctx):
        await ctx.defer()
        db = self.get_db(ctx.guild.id)
        
        embed = discord.Embed(title="🎙️ Configuration Vocal Temporaire", color=discord.Color.blue())
        embed.description = "Cliquez sur les boutons pour activer ou désactiver le salon racine."
        
        class SetupView(ui.View):
            def __init__(self, cog, db):
                super().__init__(timeout=60)
                self.cog, self.db = cog, db

            @ui.button(label="Activer", style=discord.ButtonStyle.success)
            async def v_on(self, it, btn):
                root = await it.guild.create_voice_channel("🎧│𝑻𝒐𝒏 𝒗𝒐𝒄𝒂𝒍", category=it.channel.category, user_limit=1)
                self.db["root_id"] = root.id
                self.cog.save_db(it.guild.id, self.db)
                await it.response.edit_message(content=f"✅ Salon activé : <#{root.id}>", embed=None, view=None)

            @ui.button(label="Désactiver", style=discord.ButtonStyle.danger)
            async def v_off(self, it, btn):
                if self.db["root_id"]:
                    c = it.guild.get_channel(self.db["root_id"])
                    if c: await c.delete()
                self.db["root_id"] = None
                self.cog.save_db(it.guild.id, self.db)
                await it.response.edit_message(content="❌ Système désactivé.", embed=None, view=None)

        await ctx.send(embed=embed, view=SetupView(self, db))

async def setup(bot):
    await bot.add_cog(TemporaryVoice(bot))