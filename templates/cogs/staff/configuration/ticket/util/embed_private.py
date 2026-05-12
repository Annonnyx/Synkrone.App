import discord
from discord import Embed, ButtonStyle, ui, Interaction

# --- MODAL DE RÉOUVERTURE ---
class ReopenModal(ui.Modal):
    def __init__(self, config, user_to_add):
        super().__init__(title="Réouverture du Ticket")
        self.config = config
        self.user_to_add = user_to_add
        
        self.reason = ui.TextInput(
            label="Motif de la réouverture",
            placeholder="Pourquoi réouvrez-vous ce ticket ?",
            style=discord.TextStyle.paragraph,
            required=True
        )
        self.add_item(self.reason)

    async def on_submit(self, it: Interaction):
        # 1. Remettre l'utilisateur dans le salon
        overwrites = it.channel.overwrites
        overwrites[self.user_to_add] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        
        # 2. Déplacer vers la catégorie "Ouvert"
        cat_open = it.guild.get_channel(self.config.get("category_id"))
        await it.channel.edit(category=cat_open, overwrites=overwrites)
        
        # 3. Message de confirmation et réinitialisation de la vue
        await it.response.send_message(f"🔓 **Ticket réouvert** par {it.user.mention}\n**Motif :** {self.reason.value}")
        
        # On remet le bouton Clôturer
        view = PrivateView(it.client, self.config, self.user_to_add)
        await it.message.edit(view=view)

# --- EMBED DU TICKET PRIVÉ ---
class PrivateEmbed(Embed):
    def __init__(self, user, category, subject, description, ticket_num):
        super().__init__(
            title=f"Ticket n°{ticket_num}",
            description=f"Bienvenue {user.mention} ! Le staff a été alerté et arrive pour vous aider.",
            color=0x2ecc71
        )
        self.add_field(name="📁 Motif", value=category, inline=True)
        self.add_field(name="📌 Sujet", value=f"```\n{subject}\n```", inline=False)
        self.add_field(name="📝 Description", value=f"``\n{description}\n``", inline=False)
        self.set_thumbnail(url=user.display_avatar.url)

# --- VUE AVEC LOGIQUE DYNAMIQUE ---
class PrivateView(ui.View):
    def __init__(self, bot, config, user_to_manage):
        super().__init__(timeout=None)
        self.bot = bot
        self.config = config
        self.user_to_manage = user_to_manage

    @ui.button(label="Clôturer", style=ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close(self, it: Interaction, button: ui.Button):
        # 1. Retirer l'utilisateur du salon
        overwrites = it.channel.overwrites
        overwrites[self.user_to_manage] = discord.PermissionOverwrite(read_messages=False)
        
        # 2. Déplacer dans la catégorie Archives
        cat_archive = it.guild.get_channel(self.config.get("archive_id"))
        await it.channel.edit(category=cat_archive, overwrites=overwrites)
        
        # 3. Modifier le bouton en "Réouvrir"
        self.clear_items()
        reopen_btn = ui.Button(label="Réouvrir", style=ButtonStyle.secondary, emoji="🔓", custom_id="reopen_ticket")
        reopen_btn.callback = self.reopen_callback
        self.add_item(reopen_btn)
        
        await it.response.edit_message(view=self)
        await it.followup.send(f"🔒 Ticket clôturé et archivé par {it.user.mention}.")

    async def reopen_callback(self, it: Interaction):
        # Ouvre le modal de réouverture
        await it.response.send_modal(ReopenModal(self.config, self.user_to_manage))

# --- FONCTION PRINCIPALE DE CRÉATION ---
async def create_ticket_process(it: Interaction, config, category_name, subject, description):
    guild = it.guild
    user = it.user
    
    ticket_count = config.get("ticket_count", 0) + 1
    config["ticket_count"] = ticket_count 
    
    channel_name = f"{ticket_count:04d}-{user.name}"
    support_role = guild.get_role(config.get("support_role_id"))
    category_discord = guild.get_channel(config.get("category_id"))

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
        support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
    }

    channel = await guild.create_text_channel(
        name=channel_name,
        category=category_discord,
        overwrites=overwrites
    )

    # Notification simple sans "Nouveau ticket ouvert"
    notification_msg = f"{user.mention} | {support_role.mention}"

    embed = PrivateEmbed(user, category_name, subject, description, ticket_count)
    view = PrivateView(it.client, config, user)
    
    await channel.send(content=notification_msg, embed=embed, view=view)
    
    return channel