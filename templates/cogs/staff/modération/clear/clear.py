import discord
from discord.ext import commands
from typing import Optional, Union
import traceback
from datetime import timedelta
import asyncio

# ==============================================================================
# --------------------------- ERROR UTILS --------------------------------------
# ==============================================================================
def error_print(message):
    """Affiche un message d'erreur avec la notation [CLEAR] en orange"""
    # \033[38;5;208m = Texte en orange | \033[0m = Réinitialisation de la couleur
    print(f"\033[38;5;208m[CLEAR] {message}\033[0m")

# ==============================================================================
# --------------------------- IMPORTATION UTILS --------------------------------
# ==============================================================================
try:
    from cogs.addons.embed_type.utils import config_manager
except ImportError:
    config_manager = None

class Clear(commands.Cog):
    """🗑️ Système de purge multi-utilisateurs."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def create_embed(self, ctx, title, description):
        if config_manager:
            return config_manager.get_formatted_embed(
                guild=ctx.guild, user=ctx.author, bot=self.bot,
                title=title, description=description
            )
        return discord.Embed(title=title, description=description, color=discord.Color.blue())

    @commands.hybrid_command(
        name="clear",
        description="🗑️ Supprime des messages du salon avec options avancées"
    )
    @commands.has_permissions(manage_messages=True)
    @discord.app_commands.describe(
        nombre="Nombre de messages à supprimer (ex: 10, 50, 100)",
        utilisateur1="Premier utilisateur ciblé (optionnel)",
        utilisateur2="Deuxième utilisateur ciblé (optionnel)",
        utilisateur3="Troisième utilisateur ciblé (optionnel)"
    )
    async def clear(
        self,
        ctx: commands.Context,
        nombre: Optional[int] = None,
        utilisateur1: Optional[discord.Member] = None,
        utilisateur2: Optional[discord.Member] = None,
        utilisateur3: Optional[discord.Member] = None
    ):
        """
        Syntaxes supportées :
        !clear 10 -> 10 derniers messages
        !clear 50 @User1 @User2 -> 50 messages parmi les deux users
        !clear -> Tout supprimer (Admin)
        """
        
        # Vérification des permissions Discord natives
        if not ctx.author.guild_permissions.manage_messages:
            embed = self.create_embed(ctx, "🚫 Accès Refusé", "Je n'ai pas les permissions requises")
            return await ctx.send(embed=embed, ephemeral=True)
            
        await ctx.defer(ephemeral=True)

        # 1. RÉCUPÉRATION DES CIBLES (UTILISATEURS ET RÔLES)
        target_members = []
        target_roles = []
        
        if ctx.interaction:
            target_members = [m for m in [utilisateur1, utilisateur2, utilisateur3] if m]
        else:
            content = ctx.message.content.lower()
            args = content.split()[1:]  
            
            amount_from_args = None
            time_from_args = None
            
            for arg in args:
                if arg.isdigit():
                    amount_from_args = int(arg)
                elif any(arg.endswith(suffix) for suffix in ['h', 'm', 'j', 'd', 'w']):
                    time_from_args = arg
                    break
            
            if nombre is None and amount_from_args is not None:
                nombre = amount_from_args
            
            target_members = ctx.message.mentions
            target_roles = ctx.message.role_mentions
            
            for arg in args:
                if arg.startswith('<@&') and arg.endswith('>'):
                    try:
                        role_id = int(arg[3:-1])
                        role = ctx.guild.get_role(role_id)
                        if role and role not in target_roles:
                            target_roles.append(role)
                    except:
                        pass
                
                elif arg.isdigit() and len(arg) >= 17 and len(arg) <= 19:
                    user_id = int(arg)
                    role_id = int(arg)
                    
                    user = ctx.guild.get_member(user_id)
                    if user and user not in target_members:
                        target_members.append(user)
                    else:
                        role = ctx.guild.get_role(role_id)
                        if role and role not in target_roles:
                            target_roles.append(role)
                
                elif arg.startswith('<@') and arg.endswith('>') and not arg.startswith('<@&'):
                    try:
                        user_id = int(arg[2:-1])
                        user = ctx.guild.get_member(user_id)
                        if user and user not in target_members:
                            target_members.append(user)
                    except:
                        pass
            
            if nombre is None and time_from_args is not None:
                try:
                    time_str = time_from_args.lower()
                    if time_str.endswith('h'):
                        hours = int(time_str[:-1])
                        delta = timedelta(hours=hours)
                    elif time_str.endswith('m'):
                        minutes = int(time_str[:-1])
                        delta = timedelta(minutes=minutes)
                    elif time_str.endswith('j') or time_str.endswith('d'):
                        days = int(time_str[:-1])
                        delta = timedelta(days=days)
                    elif time_str.endswith('w'):
                        weeks = int(time_str[:-1])
                        delta = timedelta(weeks=weeks)
                    else:
                        embed = self.create_embed(ctx, "❌ Format invalide", "Utilisez: 1h, 30m, 2j, 1w")
                        return await ctx.send(embed=embed, ephemeral=True)
                    
                    cutoff_time = discord.utils.utcnow() - delta
                    fourteen_days_ago = discord.utils.utcnow() - timedelta(days=14)
                    
                    if cutoff_time < fourteen_days_ago:
                        cutoff_time = fourteen_days_ago
                        embed = self.create_embed(ctx, "⚠️ Limite Discord", "Les messages de plus de 14 jours ne peuvent pas être supprimés en masse.")
                        return await ctx.send(embed=embed, ephemeral=True)
                    
                    def check_time(m):
                        return m.created_at > cutoff_time
                    
                    if target_members or target_roles:
                        member_ids = [m.id for m in target_members]
                        
                        if target_roles:
                            for role in target_roles:
                                role_members = [member.id for member in role.members]
                                member_ids.extend(role_members)
                            member_ids = list(set(member_ids)) 
                        
                        def check_combined(m):
                            if not check_time(m):
                                return False
                            return m.author.id in member_ids
                        
                        deleted_messages = await ctx.channel.purge(limit=None, check=check_combined)
                        count = len(deleted_messages)
                        
                        target_parts = []
                        if target_members:
                            target_parts.append(", ".join([m.mention for m in target_members]))
                        if target_roles:
                            target_parts.append(", ".join([r.mention for r in target_roles]))
                        
                        targets_text = " et ".join(target_parts)
                        msg_text = f"Nettoyage de **{count}** messages de {targets_text} des derniers {time_str} terminé."
                    else:
                        deleted_messages = await ctx.channel.purge(limit=None, check=check_time)
                        count = len(deleted_messages)
                        msg_text = f"Nettoyage de **{count}** messages des derniers {time_str} terminé."
                    
                    title = "🗑️ Purge effectuée"
                    msg = await ctx.send(embed=self.create_embed(ctx, title, msg_text), ephemeral=True)
                    await asyncio.sleep(10)
                    try:
                        await msg.delete()
                    except:
                        pass
                    
                except ValueError:
                    embed = self.create_embed(ctx, "❌ Format invalide", "Utilisez: 1h, 30m, 2j, 1w")
                    return await ctx.send(embed=embed, ephemeral=True)
                except discord.Forbidden:
                    error_print("Erreur Forbidden : Le bot n'a pas la permission de supprimer des messages par durée.")
                    await ctx.send("Je n'ai pas la permission")
                except Exception as e:
                    error_print(f"Erreur inattendue (purge durée) : {str(e)}")
                    await ctx.send(f"❌ Erreur: {str(e)}", ephemeral=True)
                return

        # 2. MENU INTERACTIF SI AUCUN ARGUMENT
        if nombre is None and not target_members:
            recent_users = []
            async for message in ctx.channel.history(limit=100):
                if message.author not in recent_users and not message.author.bot:
                    recent_users.append(message.author)
                    if len(recent_users) >= 24:
                        break
            
            embed = self.create_embed(
                ctx, 
                "🗑️ **Panneau de Contrôle Clear**", 
                "Configurez la suppression de messages avec les options ci-dessous"
            )
            
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            
            syntaxes_text = """
**🎯 PURGE PAR UTILISATEUR**
`/clear @user` - Supprime TOUS les messages de @user
`/clear @user 50` - Supprime les 50 derniers messages de @user  
`/clear @user 2h` - Supprime les messages de @user des 2 dernières heures

**👥 PURGE PAR RÔLE**
`/clear @role` - Supprime TOUS les messages des membres avec @role
`/clear @role 50` - Supprime les 50 derniers messages des membres avec @role
`/clear @role 2h` - Supprime les messages des membres avec @role des 2 dernières heures

**🌐 PURGE GLOBALE**
`/clear 50` - Supprime les 50 derniers messages de TOUS les utilisateurs
`/clear 2h` - Supprime les messages des 2 dernières heures de TOUS les utilisateurs

**⚙️ OPTIONS MULTIPLES**
`/clear 50 @User1 @User2` - Supprime 50 messages parmi User1 et User2

**📝 FORMAT TEMPOREL**
`1h` = 1 heure • `30m` = 30 minutes • `2j` = 2 jours • `1w` = 1 semaine
            """
            
            embed.add_field(
                name="📝 **Toutes les Syntaxes Disponibles**",
                value=syntaxes_text,
                inline=False
            )
            
            embed.timestamp = discord.utils.utcnow()
            
            class AmountModal(discord.ui.Modal, title="Nombre de messages à supprimer"):
                amount = discord.ui.TextInput(
                    label="Nombre de messages",
                    placeholder="Ex: 10, 50, 100...",
                    required=True,
                    style=discord.TextStyle.short,
                    max_length=4
                )
                
                async def on_submit(self, interaction: discord.Interaction):
                    try:
                        amount = int(self.amount.value)
                        if amount <= 0:
                            await interaction.response.send_message("❌ Le nombre doit être positif", ephemeral=True)
                            return
                        if amount > 1000:
                            await interaction.response.send_message("❌ Maximum 1000 messages", ephemeral=True)
                            return
                        
                        await interaction.response.defer(ephemeral=True)
                        deleted = await ctx.channel.purge(limit=amount)
                        msg = await interaction.followup.send(f"✅ **{len(deleted)}** messages supprimés", ephemeral=True)
                        await asyncio.sleep(10)
                        try:
                            await msg.delete()
                        except:
                            pass
                    except ValueError:
                        error_print("Erreur AmountModal : L'utilisateur n'a pas entré un nombre valide.")
                        await interaction.response.send_message("❌ Veuillez entrer un nombre valide", ephemeral=True)
                    except Exception as e:
                        error_print(f"Erreur inattendue (AmountModal) : {str(e)}")
                        await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)
            
            class TimeModal(discord.ui.Modal, title="Durée de suppression"):
                time = discord.ui.TextInput(
                    label="Temps (format: 1h, 30m, 2j, 1w)",
                    placeholder="Ex: 1h, 30m, 2j, 1w",
                    required=True,
                    style=discord.TextStyle.short
                )
                
                async def on_submit(self, interaction: discord.Interaction):
                    try:
                        time_str = self.time.value.lower()
                        if time_str.endswith('h'):
                            hours = int(time_str[:-1])
                            delta = timedelta(hours=hours)
                        elif time_str.endswith('m'):
                            minutes = int(time_str[:-1])
                            delta = timedelta(minutes=minutes)
                        elif time_str.endswith('j') or time_str.endswith('d'):
                            days = int(time_str[:-1])
                            delta = timedelta(days=days)
                        elif time_str.endswith('w'):
                            weeks = int(time_str[:-1])
                            delta = timedelta(weeks=weeks)
                        else:
                            await interaction.response.send_message("❌ Format invalide. Utilisez: 1h, 30m, 2j, 1w", ephemeral=True)
                            return
                        
                        await interaction.response.defer(ephemeral=True)
                        cutoff_time = discord.utils.utcnow() - delta
                        deleted = await ctx.channel.purge(limit=None, after=cutoff_time)
                        msg = await interaction.followup.send(f"✅ **{len(deleted)}** messages supprimés (derniers {time_str})", ephemeral=True)
                        await asyncio.sleep(10)
                        try:
                            await msg.delete()
                        except:
                            pass
                    except ValueError:
                        error_print("Erreur TimeModal : Format temporel invalide.")
                        await interaction.response.send_message("❌ Format invalide", ephemeral=True)
                    except Exception as e:
                        error_print(f"Erreur inattendue (TimeModal) : {str(e)}")
                        await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)
            
            class ClearView(discord.ui.View):
                def __init__(self, ctx):
                    super().__init__(timeout=180.0)
                    self.ctx = ctx
                
                async def interaction_check(self, interaction: discord.Interaction) -> bool:
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("🚫 Seul l'exécutant peut interagir", ephemeral=True)
                        return False
                    return True
                
                @discord.ui.select(
                    placeholder="🔧 Choisir une action de suppression",
                    custom_id="clear_action_select",
                    min_values=1,
                    max_values=1,
                    options=[
                        discord.SelectOption(
                            label="🔢 Supprimer un nombre de messages",
                            description="Spécifier le nombre exact de messages à supprimer",
                            value="amount",
                            emoji="🔢"
                        ),
                        discord.SelectOption(
                            label="⏰ Supprimer depuis une durée",
                            description="Supprimer les messages depuis une période spécifique",
                            value="time",
                            emoji="⏰"
                        ),
                        discord.SelectOption(
                            label="🧹 Supprimer tout",
                            description="Supprimer tous les messages du salon (Admin uniquement)",
                            value="all",
                            emoji="🧹"
                        )
                    ]
                )
                async def action_select(self, interaction: discord.Interaction, select: discord.ui.Select):
                    action = select.values[0]
                    
                    if action == "amount":
                        await interaction.response.send_modal(AmountModal())
                    elif action == "time":
                        await interaction.response.send_modal(TimeModal())
                    elif action == "all":
                        if not interaction.user.guild_permissions.administrator:
                            await interaction.response.send_message("🚅 **Administrateur requis** pour cette action", ephemeral=True)
                            return
                        
                        confirm_view = discord.ui.View(timeout=30.0)
                        
                        async def confirm_yes(interaction: discord.Interaction):
                            await interaction.response.defer(ephemeral=True)
                            try:
                                deleted = await ctx.channel.purge(limit=None)
                                msg = await interaction.followup.send(f"🧹 **{len(deleted)}** messages supprimés (Grand nettoyage)", ephemeral=True)
                                await asyncio.sleep(10)
                                try:
                                    await msg.delete()
                                except:
                                    pass
                            except discord.Forbidden:
                                error_print("Erreur Forbidden : Impossible de supprimer la totalité des messages du salon.")
                                await interaction.followup.send("Je n'ai pas la permission", ephemeral=True)
                            except Exception as e:
                                error_print(f"Erreur inattendue (Clear All) : {str(e)}")
                                await interaction.followup.send(f"❌ Erreur: {str(e)}", ephemeral=True)
                        
                        async def confirm_no(interaction: discord.Interaction):
                            await interaction.response.send_message("❌ Opération annulée", ephemeral=True)
                        
                        confirm_view.add_item(discord.ui.Button(label="✅ Confirmer", style=discord.ButtonStyle.danger, callback=confirm_yes))
                        confirm_view.add_item(discord.ui.Button(label="❌ Annuler", style=discord.ButtonStyle.secondary, callback=confirm_no))
                        
                        await interaction.response.send_message("⚠️ **CONFIRMATION REQUISE**\nVoulez-vous vraiment supprimer TOUS les messages du salon ?", view=confirm_view, ephemeral=True)
            
            view = ClearView(ctx)
            return await ctx.send(embed=embed, view=view, ephemeral=True)

        # 3. SÉCURITÉ ADMIN POUR LE "CLEAR TOTAL"
        if nombre is None:
            if not ctx.author.guild_permissions.administrator:
                embed = self.create_embed(ctx, "🚫 Accès Refusé", "Seul un **Administrateur** peut effectuer une suppression totale.")
                return await ctx.send(embed=embed, ephemeral=True)
            search_limit = None
        else:
            search_limit = nombre if ctx.interaction else nombre + 1

        try:
            # 4. LOGIQUE DE FILTRAGE AMÉLIORÉE
            if target_members or target_roles:
                member_ids = [m.id for m in target_members]
                
                if target_roles:
                    for role in target_roles:
                        role_members = [member.id for member in role.members]
                        member_ids.extend(role_members)
                    member_ids = list(set(member_ids))
                
                def check(m):
                    return m.author.id in member_ids
                
                deleted_messages = await ctx.channel.purge(limit=search_limit, check=check)
                count = len(deleted_messages)
                
                target_parts = []
                if target_members:
                    target_parts.append(", ".join([m.mention for m in target_members]))
                if target_roles:
                    target_parts.append(", ".join([r.mention for r in target_roles]))
                
                targets_text = " et ".join(target_parts)
                msg_text = f"Nettoyage de **{count}** messages de {targets_text} terminé."
            else:
                fourteen_days_ago = discord.utils.utcnow() - timedelta(days=14)
                
                if search_limit is not None:
                    def check_age(m):
                        return m.created_at > fourteen_days_ago
                    
                    deleted_messages = await ctx.channel.purge(limit=search_limit, check=check_age)
                    count = len(deleted_messages)
                else:
                    def check_age_total(m):
                        return m.created_at > fourteen_days_ago
                    
                    deleted_messages = await ctx.channel.purge(limit=None, check=check_age_total)
                    count = len(deleted_messages)
                
                msg_text = f"Nettoyage de **{count}** messages terminé."

            # 5. RÉPONSE
            title = "🗑️ Purge effectuée" if nombre else "🧹 Grand Nettoyage"
            msg = await ctx.send(embed=self.create_embed(ctx, title, msg_text), ephemeral=True)
            await asyncio.sleep(10)
            try:
                await msg.delete()
            except:
                pass

        except discord.Forbidden:
            error_print("Erreur Forbidden : Le bot n'a pas la permission 'manage_messages' suffisante.")
            await ctx.send("Je n'ai pas la permission")
        except discord.HTTPException:
            error_print("Erreur HTTPException : Tentative de suppression de messages datant de plus de 14 jours.")
            await ctx.send(embed=self.create_embed(ctx, "⚠️ Limite Discord", "Les messages de plus de 14 jours ne peuvent pas être supprimés en masse."), ephemeral=True)
        except Exception as e:
            error_print(f"Erreur générale lors de la suppression : {e}")
            traceback.print_exc()
            await ctx.send("❌ Une erreur est survenue.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Clear(bot))