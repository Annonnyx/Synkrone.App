from .profilIA import get_profile_embed
import asyncio
import logging
import os
import time
from collections import defaultdict, deque

import aiohttp
import discord
from discord.ext import commands

log = logging.getLogger("ia_cog")

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────

GROQ_API_KEY = ""  # chargé dans cog_load
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 10    # échanges mémorisés par utilisateur
MAX_TOKENS = 1000
TYPING_DELAY = 0.4
COOLDOWN_SECONDS = 0     # cooldown désactivé


def build_system_prompt(bot_name: str, bot_owner: str, support_url: str) -> str:
    return (
        f"Ton nom est {bot_name}. "
        f"Ton domaine d'expertise couvre Discord, la création et la gestion de bots Discord, "
        "ainsi que la programmation informatique en général. "
        "Tu ne dois pas suggérer de commandes, étant donné que tu risquerais de proposer "
        "des commandes qui n'existent pas ou qui ne sont pas adaptées au contexte. "
        "Cependant la commande ``!help`` est toujours disponible pour guider les utilisateurs. "
        "Règles de comportement : "
        "- Adopte le ton d'un manager d'entreprise : tes réponses doivent être courtes mais, "
        "professionnelles & compréhensibles. "
        "- Réponds en français par défaut, mais adapte-toi automatiquement si l'utilisateur "
        "te parle dans une autre langue. "
        "- Limite l'utilisation du formatage Markdown au strict nécessaire, réserve-le "
        "principalement aux blocs de code informatique. "
        "- Ton objectif principal est d'assister efficacement les membres du serveur dans leurs requêtes. "
        "- le `!help` doit toujours être entre ``"
        "Déclencheurs de réponses spécifiques (à respecter à la lettre) : "
        f"- Sur ton origine/créateur : Si l'on t'interroge sur ton développeur ou ton auteur, "
        f"réponds : 'Je suis développé par {bot_owner}.' "
        f"- Sur le support : Si quelqu'un demande le serveur de support, ou comment contacter, "
        f"réponds : ':link: Besoin d'aide ? Rejoignez {support_url}' "
        "- Sur l'utilisation : Si quelqu'un ne sait pas comment t'utiliser ou demande de l'aide "
        "générale sur le bot, réponds : 'Pour découvrir toutes les fonctionnalités, "
        "utilisez la commande `!help` !'"
    )


class IACog(commands.Cog):
    """Chatbot IA — répond aux mentions et aux réponses à ses messages."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._histories: dict[int, deque] = defaultdict(lambda: deque(maxlen=MAX_HISTORY * 2))
        self._cooldowns: dict[int, float] = {}
        self._session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        global GROQ_API_KEY
        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self._session = aiohttp.ClientSession()

        bot_name = os.getenv("BOT_NAME", "SynkroneBot")
        bot_owner = os.getenv("BOT_OWNER", "Synkrone")
        support_url = os.getenv("SUPPORT_URL", "https://discord.gg/p768u2Pgp3")
        self._system_prompt = build_system_prompt(bot_name, bot_owner, support_url)

        log.info(
            "IACog chargé — modèle : %s | clé : %s | bot : %s",
            MODEL,
            f"{GROQ_API_KEY[:12]}..." if GROQ_API_KEY else "MANQUANTE",
            bot_name,
        )

    async def cog_unload(self):
        if self._session:
            await self._session.close()

    async def _ask(self, user_id: int, user_message: str) -> str:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY manquante dans le .env")

        history = self._histories[user_id]
        history.append({"role": "user", "content": user_message})

        messages = [{"role": "system", "content": self._system_prompt}] + list(history)

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL,
            "messages": messages,
            "max_tokens": MAX_TOKENS,
        }

        async with self._session.post(GROQ_URL, json=payload, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise ConnectionError(f"HTTP {resp.status} — {text[:200]}")
            data = await resp.json()

        reply = data["choices"][0]["message"]["content"].strip()
        history.append({"role": "assistant", "content": reply})
        return reply

    def _should_respond(self, message: discord.Message) -> bool:
        # 1. Ignorer les bots
        if message.author.bot:
            return False

        # 2. Ignorer si ce n'est PAS un serveur (donc MP/DM)
        if message.guild is None:
            return False

        # 3. Répondre si mentionné
        if self.bot.user in message.mentions:
            return True

        # 4. Répondre si c'est une réponse à un message du bot
        if (
            message.reference
            and isinstance(message.reference.resolved, discord.Message)
            and message.reference.resolved.author == self.bot.user
        ):
            return True
        return False

    def _clean_content(self, message: discord.Message) -> str:
        content = message.content
        if self.bot.user:
            content = content.replace(f"<@{self.bot.user.id}>", "").strip()
            content = content.replace(f"<@!{self.bot.user.id}>", "").strip()
        return content.strip()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self._should_respond(message):
            return

        content = self._clean_content(message)
        if not content:
            return

        # Vérification cooldown
        now = time.monotonic()
        last = self._cooldowns.get(message.author.id, 0.0)
        remaining = COOLDOWN_SECONDS - (now - last)
        if remaining > 0:
            await message.reply(
                f"⏳ Attends encore **{int(remaining) + 1}s** avant de me reparler.",
                mention_author=False,
            )
            return
        self._cooldowns[message.author.id] = now

        async with message.channel.typing():
            await asyncio.sleep(TYPING_DELAY)

            lower_content = content.lower()
            triggers = [
                "affiche mon profil", "mon profil", "affiche le profil de",
                "profil de ", "montre le profil de", "voir le profil de",
                "qui suis-je", "comment je m'appelle"
            ]

            # Profil de soi-même
            if any(t in lower_content for t in triggers[:2]):
                embed = get_profile_embed(message.author, message.guild)
                await message.reply(embed=embed, mention_author=False)
                return

            # Profil d'un autre utilisateur mentionné
            if any(t in lower_content for t in triggers[2:]):
                if message.mentions:
                    target = next((m for m in message.mentions if m != self.bot.user), None)
                    if target:
                        embed = get_profile_embed(target, message.guild)
                        await message.reply(embed=embed, mention_author=False)
                        return

            try:
                reply = await self._ask(message.author.id, content)
            except Exception as e:
                log.error(f"Erreur IA: {e}")
                await message.reply(f"❌ Une erreur est survenue : {e}", mention_author=False)
                return

        # Gestion de l'envoi (Message long ou court)
        if len(reply) <= 1900:
            await message.reply(reply, mention_author=False)
        else:
            import tempfile
            code = reply
            if reply.strip().startswith("```") and reply.strip().endswith("```"):
                code = reply.strip()[3:-3].strip()

            with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt", encoding="utf-8") as tmp:
                tmp.write(code)
                tmp_name = tmp.name

            file = discord.File(tmp_name, filename="reponse.txt")
            await message.channel.send(
                "La réponse est trop longue pour Discord, voici un fichier texte :", file=file
            )

    @commands.command(name="ia-reset", aliases=["ia_reset"])
    async def ia_reset(self, ctx: commands.Context):
        """Réinitialise ta mémoire de conversation avec l'IA."""
        self._histories[ctx.author.id].clear()
        await ctx.reply("🧠 Mémoire réinitialisée. On repart de zéro !", mention_author=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(IACog(bot))
