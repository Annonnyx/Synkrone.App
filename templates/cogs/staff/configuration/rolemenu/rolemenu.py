import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re
from typing import List, Dict, Optional

# --- IMPORT CONFIG MANAGER ---
# On tente une importation absolue classique, et on met un fallback si ça échoue.
try:
    from cogs.staff.developpeur.commands.embed_type.utils import config_manager
except ImportError:
    config_manager = None

# --- GESTIONNAIRE DE DONNÉES ---
class RoleMenuData:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        if not os.path.exists(self.data_dir): os.makedirs(self.data_dir)
    
    def get_menu_path(self, guild_id: int, menu_name: str):
        g_dir = os.path.join(self.data_dir, str(guild_id))
        if not os.path.exists(g_dir): os.makedirs(g_dir)
        return os.path.join(g_dir, f"menu_roles_{menu_name}.json")

    def list_menus(self, guild_id: int) -> List[str]:
        g_dir = os.path.join(self.data_dir, str(guild_id))
        if not os.path.exists(g_dir): return []
        files = [(f[11:-5], os.path.getctime(os.path.join(g_dir, f))) 
                 for f in os.listdir(g_dir) if f.startswith("menu_roles_")]
        files.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in files]

    def save_menu(self, guild_id: int, menu_name: str, data: Dict):
        with open(self.get_menu_path(guild_id, menu_name), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_menu(self, guild_id: int, menu_name: str) -> Optional[Dict]:
        path = self.get_menu_path(guild_id, menu_name)
        return json.load(open(path, 'r', encoding='utf-8')) if os.path.exists(path) else None

    def delete_menu(self, guild_id: int, menu_name: str):
        path = self.get_menu_path(guild_id, menu_name)
        if os.path.exists(path): os.remove(path)

# --- VUE UTILISATEUR (PUBLIC) ---
class RoleMenuView(discord.ui.View):
    def __init__(self, data: Dict, guild_id: int, menu_name: str):
        super().__init__(timeout=None)
        self.data = data
        self.guild_id = guild_id
        self.menu_name = menu_name
        self.add_components()

    def add_components(self):
        roles = self.data.get('roles', {})
        if not roles: return

        if self.data.get('display_type') == 'buttons':
            # Mode Boutons
            for r_id, r_info in roles.items():
                btn = discord.ui.Button(
                    label=r_info['label'], 
                    emoji=r_info['emoji'],
                    custom_id=f"rm_{self.menu_name}_{r_id}", # ID unique incluant le nom du menu
                    style=discord.ButtonStyle.gray
                )
                btn.callback = self.create_callback(r_id)
                self.add_item(btn)
        else:
            # Mode Menu Déroulant
            options = []
            for k, v in roles.items():
                options.append(discord.SelectOption(
                    label=v['label'], 
                    value=k, 
                    emoji=v['emoji'], 
                    description=v['description'][:100] # Limite discord 100 chars
                ))
            
            if not options: return

            select = discord.ui.Select(
                placeholder="Choisissez vos rôles...",
                options=options,
                min_values=0,
                max_values=len(options) if self.data.get('selection_mode') == 'multiple' else 1,
                custom_id=f"rm_select_{self.menu_name}"
            )
            select.callback = self.create_select_callback()
            self.add_item(select)

    def create_callback(self, r_id):
        async def cb(interaction: discord.Interaction):
            await self.toggle_roles(interaction, [int(r_id)])
        return cb

    def create_select_callback(self):
        async def cb(interaction: discord.Interaction):
            await self.toggle_roles(interaction, [int(v) for v in interaction.data['values']])
        return cb

    async def toggle_roles(self, interaction: discord.Interaction, role_ids: List[int]):
        # Vérification des restrictions
        data = self.data
        guild = interaction.guild
        member = interaction.user

        # Rôle requis
        if data.get('required_role'):
            req_id = int(data['required_role'])
            if not member.get_role(req_id):
                return await interaction.response.send_message("⛔ Vous n'avez pas le rôle requis pour utiliser ce menu.", ephemeral=True)

        # Rôle interdit
        if data.get('forbidden_role'):
            forb_id = int(data['forbidden_role'])
            if member.get_role(forb_id):
                return await interaction.response.send_message("⛔ Vous avez un rôle qui vous empêche d'utiliser ce menu.", ephemeral=True)

        added = []
        removed = []
        
        # Logique d'attribution
        if data.get('selection_mode') == 'unique':
            # Mode unique : on retire les autres rôles du menu et on met le nouveau
            menu_roles_ids = [int(k) for k in data['roles'].keys()]
            for rid in menu_roles_ids:
                role = guild.get_role(rid)
                if role and role in member.roles and rid not in role_ids:
                    await member.remove_roles(role)
            
            # Ajout du nouveau
            target_role = guild.get_role(role_ids[0])
            if target_role:
                if target_role not in member.roles:
                    await member.add_roles(target_role)
                    added.append(target_role.name)
                else:
                    # Si on clique sur celui qu'on a déjà, on peut le retirer (optionnel, comportement toggle)
                    await member.remove_roles(target_role)
                    removed.append(target_role.name)
        else:
            # Mode multiple
            for rid in role_ids:
                role = guild.get_role(rid)
                if not role: continue
                
                if role in member.roles:
                    await member.remove_roles(role)
                    removed.append(role.name)
                else:
                    await member.add_roles(role)
                    added.append(role.name)

        msg = ""
        if added: msg += f"✅ Ajouté : {', '.join(added)}\n"
        if removed: msg += f"❌ Retiré : {', '.join(removed)}"
        
        if not msg: msg = "Aucun changement."
        
        await interaction.response.send_message(msg, ephemeral=True)

# --- VUES ADMIN (CONFIGURATION) ---

class RoleOptionEditView(discord.ui.View):
    """Configuration individuelle d'un rôle"""
    def __init__(self, cog, guild_id, menu_name, role_id, user_id):
        super().__init__(timeout=300)
        self.cog = cog
        self.guild_id = guild_id
        self.menu_name = menu_name
        self.role_id = role_id
        self.user_id = user_id
        self.data_manager = RoleMenuData()

    def create_embed(self):
        data = self.data_manager.load_menu(self.guild_id, self.menu_name)
        if not data or self.role_id not in data['roles']:
            return discord.Embed(title="Erreur", description="Rôle introuvable.")
            
        r = data['roles'][self.role_id]
        title = f"🛠️ Édition : {r['label']}"
        desc = (f"📌 **Rôle :** <@&{self.role_id}>\n\n"
                f"🔹 **Nom dans le menu :** `{r['label']}`\n"
                f"🔹 **Emoji :** {r['emoji']}\n"
                f"🔹 **Description :** {r['description']}")
                
        if self.cog.config_manager:
            embed = self.cog.config_manager.get_formatted_embed(
                guild=self.cog.bot.get_guild(self.guild_id), 
                user=self.cog.bot.get_user(self.user_id), 
                bot=self.cog.bot,
                title=title,
                description=desc
            )
        else:
            embed = discord.Embed(title=title, description=desc, color=0x2b2d31)
            
        return embed

    @discord.ui.button(label="Nom & Description", style=discord.ButtonStyle.gray, emoji="📝")
    async def edit_name_desc(self, interaction, button): await self.open_name_desc_modal(interaction)
    
    @discord.ui.button(label="Emoji", style=discord.ButtonStyle.gray, emoji="😀")
    async def edit_emoji(self, interaction, button): 
        self.cog.active_emoji_configs[f"{self.guild_id}_{self.user_id}"] = {
            "menu": self.menu_name, 
            "role_id": self.role_id,
            "message_id": interaction.message.id, 
            "channel_id": interaction.channel.id
        }
        await interaction.response.send_message("Envoyez le nouvel emoji dans le chat maintenant.", ephemeral=True)

    @discord.ui.button(label="Supprimer du menu", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_r(self, interaction, button):
        data = self.data_manager.load_menu(self.guild_id, self.menu_name)
        if self.role_id in data['roles']:
            data['roles'].pop(self.role_id)
            self.data_manager.save_menu(self.guild_id, self.menu_name, data)
            await self.cog.update_deployed_messages(self.guild_id, self.menu_name)
        
        v = RoleMenuDetailView(self.cog, self.guild_id, self.menu_name, self.user_id)
        await interaction.response.edit_message(embed=v.create_embed(), view=v)

    @discord.ui.button(label="Retour", style=discord.ButtonStyle.blurple, emoji="⬅️")
    async def back(self, interaction, button):
        v = RoleMenuDetailView(self.cog, self.guild_id, self.menu_name, self.user_id)
        await interaction.response.edit_message(embed=v.create_embed(), view=v)

    async def open_name_desc_modal(self, interaction):
        data = self.data_manager.load_menu(self.guild_id, self.menu_name)
        r = data['roles'][self.role_id]
        
        modal = discord.ui.Modal(title="Modifier Nom & Description")
        name_input = discord.ui.TextInput(label="Nom", default=r['label'], required=True)
        desc_input = discord.ui.TextInput(label="Description", default=r['description'], required=False, style=discord.TextStyle.paragraph)
        modal.add_item(name_input)
        modal.add_item(desc_input)
        
        async def cb(inter):
            data = self.data_manager.load_menu(self.guild_id, self.menu_name)
            data['roles'][self.role_id]['label'] = name_input.value
            data['roles'][self.role_id]['description'] = desc_input.value or ''
            self.data_manager.save_menu(self.guild_id, self.menu_name, data)
            await self.cog.update_deployed_messages(self.guild_id, self.menu_name)
            await inter.response.edit_message(embed=self.create_embed(), view=self)
        modal.on_submit = cb
        await interaction.response.send_modal(modal)

class RoleMenuDetailView(discord.ui.View):
    """Configuration globale du menu"""
    def __init__(self, cog, guild_id, menu_name, user_id):
        super().__init__(timeout=600)
        self.cog = cog
        self.guild_id = guild_id
        self.menu_name = menu_name
        self.user_id = user_id
        self.data_manager = RoleMenuData()
        self.setup_components()

    def setup_components(self):
        data = self.data_manager.load_menu(self.guild_id, self.menu_name)
        if not data: return

        # 1. Sélecteur d'Actions
        act_select = discord.ui.Select(placeholder="⚙️ Configurer le menu...", options=[
            discord.SelectOption(label="Renommer le menu", value="rename", emoji="✏️"),
            discord.SelectOption(label="Mode (Unique/Multiple)", value="mode", emoji="🔄"),
            discord.SelectOption(label="Type (Boutons/Sélecteur)", value="type", emoji="🎨"),
            discord.SelectOption(label="Restrictions d'accès", value="access", emoji="🔒"),
            discord.SelectOption(label="Supprimer le menu", value="delete", emoji="🗑️")
        ], row=0)
        act_select.callback = self.action_callback
        self.add_item(act_select)

        # 2. Sélecteur de Rôles
        roles = data.get('roles', {})
        if roles:
            options = []
            for k, v in roles.items():
                options.append(discord.SelectOption(label=v['label'], value=k, emoji=v['emoji']))
            
            # Pagination simple si trop de rôles (max 25)
            if len(options) > 25: options = options[:25]
            
            role_select = discord.ui.Select(placeholder="🎭 Modifier un rôle spécifique...", options=options, row=1)
            role_select.callback = self.role_config_callback
            self.add_item(role_select)

    def create_embed(self):
        data = self.data_manager.load_menu(self.guild_id, self.menu_name)
        if not data: return discord.Embed(title="Erreur", description="Menu introuvable.")

        roles = data.get('roles', {})
        guild = self.cog.bot.get_guild(self.guild_id)
        
        req_role_name = "Aucun"
        if data.get('required_role'):
            req_role = guild.get_role(int(data.get('required_role')))
            req_role_name = req_role.name if req_role else "Rôle introuvable"
        
        inter_role_name = "Aucun"
        if data.get('forbidden_role'):
            inter_role = guild.get_role(int(data.get('forbidden_role')))
            inter_role_name = inter_role.name if inter_role else "Rôle introuvable"
        
        mode_text = "Unique (1 seul choix)" if data.get('selection_mode') == 'unique' else "Multiple (Plusieurs choix)"
        type_text = "Boutons" if data.get('display_type') == 'buttons' else "Menu déroulant"
        
        deploy_status = f"[📄 Voir le message]({data.get('deploy_url')})" if data.get('deploy_url') else "❌ Non déployé"

        role_list_str = "\n".join([f"   └ {v['emoji']} **{v['label']}**" for k,v in roles.items()]) if roles else "   └ _Aucun rôle configuré_"

        title = f"📂 Menu : {self.menu_name.replace('_', ' ').title()}"
        desc = (f"⚙️ **Configuration**\n"
                f"• Mode : `{mode_text}`\n"
                f"• Type : `{type_text}`\n\n"
                f"🔒 **Restrictions**\n"
                f"• Requis : {req_role_name}\n"
                f"• Interdit : {inter_role_name}\n\n"
                f"🚀 **État** : {deploy_status}\n\n"
                f"🎭 **Rôles ({len(roles)})**\n{role_list_str}")
                
        if self.cog.config_manager:
            embed = self.cog.config_manager.get_formatted_embed(
                guild=self.cog.bot.get_guild(self.guild_id), 
                user=self.cog.bot.get_user(self.user_id), 
                bot=self.cog.bot,
                title=title,
                description=desc
            )
        else:
            embed = discord.Embed(title=title, description=desc, color=0x2b2d31)
            
        return embed

    async def action_callback(self, interaction: discord.Interaction):
        action = interaction.data['values'][0]
        data = self.data_manager.load_menu(self.guild_id, self.menu_name)

        if action == "rename":
            modal = discord.ui.Modal(title="Renommer le menu")
            name_input = discord.ui.TextInput(label="Nouveau nom", default=self.menu_name.replace("_", " "), required=True)
            modal.add_item(name_input)
            
            async def submit_callback(inter):
                new_name = name_input.value.strip().replace(" ", "_")
                if new_name and new_name != self.menu_name:
                    old_data = self.data_manager.load_menu(self.guild_id, self.menu_name)
                    self.data_manager.save_menu(self.guild_id, new_name, old_data)
                    self.data_manager.delete_menu(self.guild_id, self.menu_name)
                    self.menu_name = new_name
                    v = RoleMenuDetailView(self.cog, self.guild_id, self.menu_name, self.user_id)
                    await inter.response.edit_message(embed=v.create_embed(), view=v)
                else:
                    await inter.response.edit_message(embed=self.create_embed(), view=self)
            modal.on_submit = submit_callback
            await interaction.response.send_modal(modal)
            
        elif action == "mode":
            # Alterne entre 'unique' et 'multiple'
            data['selection_mode'] = 'unique' if data.get('selection_mode') == 'multiple' else 'multiple'
            await self.save_and_refresh(data, interaction)

        elif action == "type":
            # Alterne entre 'buttons' et 'select'
            data['display_type'] = 'buttons' if data.get('display_type') == 'select' else 'select'
            await self.save_and_refresh(data, interaction)

        elif action == "access":
            modal = discord.ui.Modal(title="Restrictions d'accès")
            req_input = discord.ui.TextInput(label="ID rôle requis (vide = aucun)", default=str(data.get('required_role', '') or ''), required=False)
            inter_input = discord.ui.TextInput(label="ID rôle interdit (vide = aucun)", default=str(data.get('forbidden_role', '') or ''), required=False)
            modal.add_item(req_input)
            modal.add_item(inter_input)
            
            async def submit_callback(inter):
                data['required_role'] = req_input.value.strip() or None
                data['forbidden_role'] = inter_input.value.strip() or None
                await self.save_and_refresh(data, inter)
            modal.on_submit = submit_callback
            await interaction.response.send_modal(modal)
            
        elif action == "delete":
            self.data_manager.delete_menu(self.guild_id, self.menu_name)
            v = RoleMenuMainView(self.cog, self.guild_id, self.user_id)
            await interaction.response.edit_message(embed=v.create_embed(), view=v)

    async def save_and_refresh(self, data, interaction):
        """Sauvegarde les données, met à jour le message public et rafraîchit l'interface admin"""
        # 1. Sauvegarde locale
        self.data_manager.save_menu(self.guild_id, self.menu_name, data)
        
        # 2. Mise à jour du message déployé (le menu public)
        await self.cog.update_deployed_messages(self.guild_id, self.menu_name)
        
        # 3. Rafraîchissement de la vue admin actuelle
        # On recrée une vue pour que les nouveaux réglages soient pris en compte dans l'affichage
        new_view = RoleMenuDetailView(self.cog, self.guild_id, self.menu_name, self.user_id)
        
        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=new_view.create_embed(), view=new_view)
        else:
            # Si on vient d'un Modal, on utilise message.edit
            await interaction.message.edit(embed=new_view.create_embed(), view=new_view)

    async def role_config_callback(self, interaction: discord.Interaction):
        view = RoleOptionEditView(self.cog, self.guild_id, self.menu_name, interaction.data['values'][0], self.user_id)
        await interaction.response.edit_message(embed=view.create_embed(), view=view)

    @discord.ui.button(label="Ajouter des Rôles", style=discord.ButtonStyle.success, emoji="➕", row=2)
    async def add_roles(self, interaction, button):
        self.cog.active_menu_configs[f"{self.guild_id}_{self.user_id}"] = {
            "menu": self.menu_name, 
            "message_id": interaction.message.id, 
            "channel_id": interaction.channel.id
        }
        await interaction.response.send_message(
            "📝 **Mode Ajout** : Envoyez les **IDs** des rôles ou **mentionnez-les** (@Role) dans ce salon.\n"
            "Vous pouvez en envoyer plusieurs d'un coup.", 
            ephemeral=True
        )

    @discord.ui.button(label="Déployer", style=discord.ButtonStyle.primary, emoji="🚀", row=2)
    async def deploy(self, interaction, button):
        data = self.data_manager.load_menu(self.guild_id, self.menu_name)
        current_url = data.get('deploy_url', '')
        current_id = current_url.split('/')[-1] if current_url else ''
        
        modal = discord.ui.Modal(title="Attacher à un message du Bot")
        mid = discord.ui.TextInput(
            label="ID du message", 
            default=current_id,
            placeholder="Laissez vide pour désactiver",
            required=False
        )
        modal.add_item(mid)
        async def cb(inter):
            msg_id_str = mid.value.strip()
            if not msg_id_str:
                # Désactiver
                data['deploy_url'] = None
                self.data_manager.save_menu(self.guild_id, self.menu_name, data)
                key = f"{self.guild_id}_{self.menu_name}"
                if key in self.cog.deployed_messages:
                    del self.cog.deployed_messages[key]
                await inter.response.edit_message(embed=self.create_embed(), view=self)
                return

            try:
                # Recherche du message
                msg = None
                try:
                    msg = await inter.channel.fetch_message(int(msg_id_str))
                except:
                    for channel in inter.guild.text_channels:
                        try:
                            msg = await channel.fetch_message(int(msg_id_str))
                            break
                        except: continue
                
                if not msg:
                    return await inter.response.send_message("❌ Message introuvable.", ephemeral=True)
                
                if msg.author.id != self.cog.bot.user.id:
                    return await inter.response.send_message("❌ Le message doit être envoyé par le bot.", ephemeral=True)

                await msg.edit(view=RoleMenuView(data, self.guild_id, self.menu_name))
                data['deploy_url'] = msg.jump_url
                self.data_manager.save_menu(self.guild_id, self.menu_name, data)
                
                key = f"{self.guild_id}_{self.menu_name}"
                self.cog.deployed_messages[key] = [{'message_id': msg.id, 'channel_id': msg.channel.id}]
                
                await inter.response.edit_message(embed=self.create_embed(), view=self)
            except Exception as e:
                await inter.response.send_message(f"❌ Erreur: {e}", ephemeral=True)

        modal.on_submit = cb
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Retour", style=discord.ButtonStyle.gray, emoji="⬅️", row=2)
    async def back(self, interaction, button):
        v = RoleMenuMainView(self.cog, self.guild_id, self.user_id)
        await interaction.response.edit_message(embed=v.create_embed(), view=v)

class RoleMenuMainView(discord.ui.View):
    def __init__(self, cog, guild_id, user_id):
        super().__init__(timeout=600)
        self.cog = cog
        self.guild_id = guild_id
        self.user_id = user_id
        self.data_manager = RoleMenuData()
        self.setup_select()

    def setup_select(self):
        menus = self.data_manager.list_menus(self.guild_id)
        if menus:
            opts = [discord.SelectOption(label=m.replace("_", " "), value=m, emoji="📁") for m in menus[:25]]
            s = discord.ui.Select(placeholder="📂 Vos Menus existants...", options=opts)
            s.callback = self.select_menu_cb
            self.add_item(s)

    async def select_menu_cb(self, interaction):
        v = RoleMenuDetailView(self.cog, self.guild_id, interaction.data['values'][0], self.user_id)
        await interaction.response.edit_message(embed=v.create_embed(), view=v)

    def create_embed(self):
        menus = self.data_manager.list_menus(self.guild_id)
        title = "🎭 Gestion des RoleMenus"
        desc = "Créez des menus interactifs pour permettre à vos membres de choisir leurs rôles.\n\n" + (f"📂 **{len(menus)} Menu(s) trouvé(s)**" if menus else "_Aucun menu. Créez-en un !_")
        
        if self.cog.config_manager:
            embed = self.cog.config_manager.get_formatted_embed(
                guild=self.cog.bot.get_guild(self.guild_id), 
                user=self.cog.bot.get_user(self.user_id), 
                bot=self.cog.bot,
                title=title,
                description=desc
            )
        else:
            embed = discord.Embed(title=title, description=desc, color=0x2b2d31)
            
        return embed

    @discord.ui.button(label="Nouveau Menu", style=discord.ButtonStyle.success, emoji="✨")
    async def create_btn(self, interaction, button):
        modal = discord.ui.Modal(title="Créer un Menu")
        name = discord.ui.TextInput(label="Nom du menu", placeholder="Ex: Rôles Jeux", required=True)
        modal.add_item(name)
        async def cb(inter):
            m_name = name.value.strip().replace(" ", "_")
            self.data_manager.save_menu(self.guild_id, m_name, {
                'name': m_name, 
                'display_type': 'select', 
                'selection_mode': 'multiple', 
                'roles': {}
            })
            v = RoleMenuDetailView(self.cog, self.guild_id, m_name, self.user_id)
            await inter.response.edit_message(embed=v.create_embed(), view=v)
        modal.on_submit = cb
        await interaction.response.send_modal(modal)

# --- COG PRINCIPAL ---
class RoleMenuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_manager = config_manager
        self.data_manager = RoleMenuData()
        self.active_menu_configs = {}
        self.active_emoji_configs = {}
        self.deployed_messages = {}
        self.load_deployed_messages()
    
    def load_deployed_messages(self):
        # Scan initial pour recharger les message_ids en mémoire
        if not os.path.exists(self.data_manager.data_dir): return
        for g_dir in os.listdir(self.data_manager.data_dir):
            path = os.path.join(self.data_manager.data_dir, g_dir)
            if os.path.isdir(path):
                for f in os.listdir(path):
                    if f.startswith("menu_roles_"):
                        try:
                            data = json.load(open(os.path.join(path, f), 'r', encoding='utf-8'))
                            if data.get('deploy_url'):
                                # Parsing correct de l'URL Discord
                                deploy_url = data['deploy_url']
                                parts = deploy_url.split('/')
                                if len(parts) >= 4:
                                    channel_id = int(parts[-2])
                                    message_id = int(parts[-1])
                                    # Extraire le nom du menu depuis le nom du fichier
                                    menu_name = f[11:-5]  # Enlever "menu_roles_" et ".json"
                                    key = f"{g_dir}_{menu_name}"
                                    self.deployed_messages[key] = [{'message_id': message_id, 'channel_id': channel_id}]
                                    # Menu chargé silencieusement
                        except Exception as e:
                            print(f"[DEBUG] Erreur chargement fichier {f}: {e}")
                            continue

    async def update_deployed_messages(self, guild_id: int, menu_name: str):
        """Met à jour tous les messages déployés pour un menu spécifique avec gestion d'erreurs"""
        key = f"{guild_id}_{menu_name}"
        if key not in self.deployed_messages: return
        
        data = self.data_manager.load_menu(guild_id, menu_name)
        if not data: 
            print(f"[DEBUG] Menu {menu_name} introuvable pour mise à jour")
            return
        
        if not data.get('roles'):
            print(f"[DEBUG] Menu {menu_name} sans rôles pour mise à jour")
            return
        
        # Créer la vue persistante une seule fois
        persistent_view = RoleMenuView(data, guild_id, menu_name)
        self.bot.add_view(persistent_view)
        
        valid_messages = []
        
        for msg_info in self.deployed_messages[key]:
            try:
                channel = self.bot.get_channel(msg_info['channel_id'])
                if not channel:
                    print(f"[DEBUG] Canal {msg_info['channel_id']} introuvable pour mise à jour de {menu_name}")
                    continue
                    
                message = await channel.fetch_message(msg_info['message_id'])
                
                # Mettre à jour le message avec la vue persistante
                await message.edit(view=persistent_view)
                valid_messages.append(msg_info)
                print(f"[DEBUG] Message {msg_info['message_id']} mis à jour pour {menu_name}")
                
            except discord.NotFound:
                print(f"[DEBUG] Message {msg_info['message_id']} introuvable lors de la mise à jour de {menu_name}")
                continue
            except discord.Forbidden:
                print(f"[DEBUG] Pas d'autorisation pour message {msg_info['message_id']} lors de la mise à jour de {menu_name}")
                continue
            except Exception as e:
                print(f"[DEBUG] Erreur inattendue lors mise à jour message {msg_info['message_id']}: {e}")
                continue
        
        # Mettre à jour la liste des messages valides
        self.deployed_messages[key] = valid_messages
        print(f"[DEBUG] Mise à jour terminée pour {menu_name}: {len(valid_messages)} messages valides")

    @commands.Cog.listener()
    async def on_ready(self):
        """Restaure les vues persistantes au reboot avec gestion d'erreurs robuste"""
        # Restauration silencieuse des vues des messages déployés
        
        for key, msgs in self.deployed_messages.items():
            try:
                gid, mname = key.split('_', 1)
                guild_id = int(gid)
                
                # Charger les données du menu
                data = self.data_manager.load_menu(guild_id, mname)
                if not data:
                    # Menu {mname} introuvable, suppression silencieuse
                    del self.deployed_messages[key]
                    continue
                
                # Vérifier que le menu a des rôles
                if not data.get('roles'):
                    print(f"[DEBUG] Menu {mname} vide, nettoyage des données orphelines")
                    del self.deployed_messages[key]
                    # Supprimer le fichier JSON du menu vide
                    try:
                        self.data_manager.delete_menu(guild_id, mname)
                        print(f"[DEBUG] Menu {mname} supprimé (plus de rôles)")
                    except Exception as e:
                        print(f"[DEBUG] Erreur lors de la suppression du menu {mname}: {e}")
                    continue
                
                # Restaurer chaque message déployé pour ce menu
                for msg_info in msgs:
                    try:
                        channel = self.bot.get_channel(msg_info['channel_id'])
                        if not channel:
                            # Canal {msg_info['channel_id']} introuvable pour {mname}
                            continue
                            
                        message = await channel.fetch_message(msg_info['message_id'])
                        
                        # Créer et attacher la vue persistante
                        view = RoleMenuView(data, guild_id, mname)
                        self.bot.add_view(view)
                        
                        # Mettre à jour le message avec la vue restaurée
                        await message.edit(view=view)
                        # Vue restaurée silencieusement pour {mname}
                        
                    except discord.NotFound:
                        print(f"[DEBUG] Message {msg_info['message_id']} introuvable pour {mname}")
                        # Marquer ce message comme invalide mais garder les autres
                        continue
                    except discord.Forbidden:
                        print(f"[DEBUG] Pas d'autorisation pour le message {msg_info['message_id']} pour {mname}")
                        continue
                    except Exception as e:
                        print(f"[DEBUG] Erreur inattendue pour message {msg_info['message_id']}: {e}")
                        continue
                        
            except ValueError as e:
                print(f"[DEBUG] Erreur de format pour la clé {key}: {e}")
                continue
            except Exception as e:
                # Erreur générale pour {key}: {e}
                continue
        
        # Restauration silencieuse terminée

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        
        # 1. GESTION DES EMOJIS (MODIFICATION)
        emoji_key = f"{message.guild.id}_{message.author.id}"
        if emoji_key in self.active_emoji_configs:
            cfg = self.active_emoji_configs[emoji_key]
            if message.channel.id != cfg["channel_id"]: return
            
            # Détection Emoji (Custom ou Unicode)
            custom_emoji = re.search(r'<a?:[a-zA-Z0-9_]+:\d+>', message.content)
            emoji = custom_emoji.group(0) if custom_emoji else message.content.strip()
            
            # Sauvegarde
            data = self.data_manager.load_menu(message.guild.id, cfg["menu"])
            if cfg["role_id"] in data['roles']:
                data['roles'][cfg["role_id"]]['emoji'] = emoji
                self.data_manager.save_menu(message.guild.id, cfg["menu"], data)
                
                await message.delete()
                await self.update_deployed_messages(message.guild.id, cfg["menu"])
                
                # Mise à jour de l'interface admin
                try:
                    admin_msg = await message.channel.fetch_message(cfg["message_id"])
                    v = RoleOptionEditView(self, message.guild.id, cfg["menu"], cfg["role_id"], message.author.id)
                    await admin_msg.edit(embed=v.create_embed(), view=v)
                except: pass
                
            del self.active_emoji_configs[emoji_key]
            return

        # 2. GESTION DE L'AJOUT DE RÔLES (ADD ROLES)
        menu_key = f"{message.guild.id}_{message.author.id}"
        if menu_key in self.active_menu_configs:
            cfg = self.active_menu_configs[menu_key]
            if message.channel.id != cfg["channel_id"]: return

            # Regex "Aspirateur" : Trouve n'importe quelle suite de 17 à 20 chiffres
            # Fonctionne pour : "123456789", "<@&123456789>", "id: 123456789"
            found_ids = set(re.findall(r'\d{17,20}', message.content))
            
            roles_added = []
            data = self.data_manager.load_menu(message.guild.id, cfg["menu"])

            for rid in found_ids:
                role = message.guild.get_role(int(rid))
                if role and str(role.id) not in data['roles']:
                    data['roles'][str(role.id)] = {
                        "label": role.name,
                        "emoji": "🎭",
                        "description": "Cliquez pour obtenir ce rôle"
                    }
                    roles_added.append(role.name)
            
            # Toujours nettoyer la configuration après le premier message
            del self.active_menu_configs[menu_key]
            
            if roles_added:
                self.data_manager.save_menu(message.guild.id, cfg["menu"], data)
                await self.update_deployed_messages(message.guild.id, cfg["menu"])
                
                await message.delete()
                await message.channel.send(f"✅ Ajouté(s) : {', '.join(roles_added)}\n📝 Mode ajout désactivé.", delete_after=5)
                
                # Mise à jour de l'interface admin
                try:
                    admin_msg = await message.channel.fetch_message(cfg["message_id"])
                    v = RoleMenuDetailView(self, message.guild.id, cfg["menu"], message.author.id)
                    await admin_msg.edit(embed=v.create_embed(), view=v)
                except: pass
            else:
                await message.delete()
                await message.channel.send("⚠️ Aucun nouveau rôle détecté ou rôle déjà présent.\n📝 Mode ajout désactivé.", delete_after=3)

    @commands.hybrid_command(name="rolemenu")
    @commands.has_permissions(administrator=True)
    async def rolemenu_prefix(self, ctx):
        """Commande préfixe pour gérer les rolemenus"""
        view = RoleMenuMainView(self, ctx.guild.id, ctx.author.id)
        await ctx.send(embed=view.create_embed(), view=view)

async def setup(bot):
    await bot.add_cog(RoleMenuCog(bot))