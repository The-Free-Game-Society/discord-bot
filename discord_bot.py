import logging
import os
import sys

import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

INITIAL_EXTENSIONS = [
    "cogs.dummy_cog",
]

# --- intents -------------------------------------------------------------
# Only turn on message_content / members / presences if some cog actually
# needs them - each is privileged and must ALSO be enabled in the
# Developer Portal (Bot page) or login will fail with
# PrivilegedIntentsRequired. None of the monastery cogs need them.
intents = discord.Intents.default()
intents.voice_states = True  # needed by the stage-channel bell cog
# intents.message_content = True   # uncomment only if a cog needs it
# intents.members = True           # uncomment only if a cog needs it
# intents.presences = True         # uncomment only if a cog needs it

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    stream=sys.stdout,  # so it lands in journalctl cleanly under systemd
)
log = logging.getLogger("discord_bot")
logging.getLogger("discord.gateway").setLevel(logging.WARNING)


class FGSBot(discord.Bot):
    def __init__(self):
        super().__init__(intents=intents)

    async def on_ready(self):
        log.info("Logged in as %s (id=%s)", self.user, self.user.id)
        log.info("Connected to %d guild(s)", len(self.guilds))


def main():
    if not TOKEN:
        log.critical(
            "DISCORD_BOT_TOKEN is not set. Put it in your .env file "
            "(local runs) or the systemd EnvironmentFile (production)."
        )
        sys.exit(1)

    bot = FGSBot()

    for extension in INITIAL_EXTENSIONS:
        try:
            bot.load_extension(extension)  # synchronous in py-cord, do not await
            log.info("Loaded extension: %s", extension)
        except Exception:
            log.exception("Failed to load extension: %s", extension)

    bot.run(TOKEN)  # blocking call - sets up and runs its own event loop


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Shutting down (KeyboardInterrupt)")