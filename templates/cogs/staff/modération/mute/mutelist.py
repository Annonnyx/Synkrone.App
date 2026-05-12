import discord, json, asyncio, traceback
from discord.ext import commands, tasks
from pathlib import Path

try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class MuteListView(discord.ui.View):
    def __init__(self, ctx, data, bot):
        super().__init__(timeout=120)
        self.ctx, self.data, self.bot = ctx, data, bot

    @discord.ui.select(placeholder="🔊 Sélectionner un membre pour lever sa sanction...")
    async def unmute_select(self, it: discord.Interaction, select: discord.ui.Select):
        if not it.permissions.moderate_members:
            return await it.response.send_message("❌ Permissions insuffisantes.", ephemeral=True)

        key = select.values[0]
        folder = Path(__file__).parent / "data"
        file_local = folder / f"{it.guild.id}.json"
        file_global = folder / f"{it.guild.id}_global.json"

        info, is_global = None, False

        # 1. Recherche Global
        if file_global.exists():
            try:
                dg = json.loads(file_global.read_text(encoding="utf-8"))
                if key in dg:
                    info, is_global = dg.pop(key), True
                    file_global.write_text(json.dumps(dg, indent=4), encoding="utf-8")
            except: pass

        # 2. Recherche Local
        if not info and file_local.exists():
            try:
                dl = json.loads(file_local.read_text(encoding="utf-8"))
                if key in dl:
                    info, is_global = dl.pop(key), False
                    file_local.write_text(json.dumps(dl, indent=4), encoding="utf-8")
            except: pass

        if info:
            member = it.guild.get_member(int(info.get("user_id", 0)))
            if member:
                if is_global or "_" not in key:
                    role = discord.utils.get(it.guild.roles, name="🤫│𝑴𝒖𝒆𝒕")
                    if role: await member.remove_roles(role)
                else:
                    chan_id = info.get("channel_id")
                    if chan_id:
                        channel = it.guild.get_channel(int(chan_id))
                        if channel: await channel.set_permissions(member, overwrite=None)
            
            await it.response.send_message(f"✅ Sanction levée.", ephemeral=True)
            await it.message.delete()
        else:
            await it.response.send_message("❌ Sanction introuvable.", ephemeral=True)

class MuteList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_mutes.start()

    def cog_unload(self):
        self.check_mutes.cancel()

    def create_embed(self, ctx, title, description):
        if config_manager:
            return config_manager.get_formatted_embed(guild=ctx.guild, user=ctx.author, bot=self.bot, title=title, description=description)
        return discord.Embed(title=title, description=description, color=discord.Color.blue())

    @tasks.loop(seconds=30)
    async def check_mutes(self):
        data_folder = Path(__file__).parent / "data"
        if not data_folder.exists(): return
        now = discord.utils.utcnow().timestamp()

        for file in data_folder.glob("*.json"):
            try:
                guild_id = int(file.stem.replace("_global", ""))
                guild = self.bot.get_guild(guild_id)
                if not guild: continue
                
                data = json.loads(file.read_text(encoding="utf-8"))
                to_remove = []
                is_global_file = "_global" in file.name

                for key, val in list(data.items()):
                    expires = val.get("expires_at")
                    if expires is None: 
                        to_remove.append(key) # Nettoyage donnée corrompue
                        continue

                    if expires != 9999999999 and now >= expires:
                        user_id = val.get("user_id")
                        member = guild.get_member(user_id) if user_id else None
                        
                        if is_global_file:
                            role = discord.utils.get(guild.roles, name="🤫│𝑴𝒖𝒆𝒕")
                            if member and role: 
                                try: await member.remove_roles(role)
                                except: pass
                        else:
                            chan_id = val.get("channel_id")
                            if member and chan_id:
                                channel = guild.get_channel(chan_id)
                                if channel:
                                    try: await channel.set_permissions(member, overwrite=None)
                                    except: pass
                        to_remove.append(key)

                if to_remove:
                    for k in to_remove: data.pop(k)
                    file.write_text(json.dumps(data, indent=4), encoding="utf-8")
            except Exception as e:
                print(f"[ERROR Task] {file.name}: {e}")

    @commands.hybrid_command(name="mutelist")
    @commands.has_permissions(moderate_members=True)
    async def mutelist(self, ctx):
        try:
            await ctx.defer()
            folder = Path(__file__).parent / "data"
            
            def safe_load(path):
                if not path.exists(): return {}
                try: return json.loads(path.read_text(encoding="utf-8"))
                except: return {}

            data_l = safe_load(folder / f"{ctx.guild.id}.json")
            data_g = safe_load(folder / f"{ctx.guild.id}_global.json")

            if not data_l and not data_g:
                return await ctx.send(embed=self.create_embed(ctx, "📜 Registre Vide", "Aucune sanction active."), ephemeral=True)

            view = MuteListView(ctx, {**data_l, **data_g}, self.bot)
            desc = ""
            
            if data_g:
                desc += "### 🌍 Sanctions Serveur\n"
                for k, v in data_g.items():
                    m = ctx.guild.get_member(v.get("user_id", 0))
                    name = m.name if m else f"ID: {k}"
                    exp_val = v.get("expires_at", 0)
                    exp = "∞ Permanent" if exp_val == 9999999999 else f"<t:{int(exp_val)}:R>"
                    desc += f"• **{name}** | {exp}\n"
                    view.unmute_select.add_option(label=f"{name[:20]} (Global)", value=str(k))

            if data_l:
                desc += "\n### 📍 Sanctions Salons\n"
                for k, v in data_l.items():
                    user_id = v.get("user_id", 0)
                    chan_id = v.get("channel_id")
                    
                    m = ctx.guild.get_member(user_id)
                    c = ctx.guild.get_channel(chan_id) if chan_id else None
                    
                    name = m.name if m else f"ID: {user_id}"
                    chan_name = f"#{c.name}" if c else "Inconnu"
                    exp_val = v.get("expires_at", 0)
                    exp = "∞ Permanent" if exp_val == 9999999999 else f"<t:{int(exp_val)}:R>"
                    
                    desc += f"• **{name}** | {chan_name} | {exp}\n"
                    view.unmute_select.add_option(label=f"{name[:20]} (Local)", value=str(k))

            await ctx.send(embed=self.create_embed(ctx, "📜 Liste des Sanctions", desc), view=view)
        except Exception as e:
            print(f"[ERROR Mutelist] {e}")
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(MuteList(bot))