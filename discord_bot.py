import logging
import os
import sys

import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

INITIAL_EXTENSIONS = [
    "cogs.dummy_cog",
]


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    stream=sys.stdout,  # so it lands in journalctl cleanly under systemd
)
log = logging.getLogger("discord_bot")
logging.getLogger("discord.gateway").setLevel(logging.WARNING)


class FGSBot(discord.Bot):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())

    async def on_ready(self):
        log.info("Logged in as %s (id=%s)", self.user, self.user.id)
        log.info("Connected to %d guild(s)", len(self.guilds))


def main():
    if not TOKEN:
        log.critical("DISCORD_BOT_TOKEN is not set. Put it in your .env file.")
        sys.exit(1)

    bot = FGSBot()

    for extension in INITIAL_EXTENSIONS:
        try:
            bot.load_extension(extension)
            log.info("Loaded extension: %s", extension)
        except Exception:
            log.exception("Failed to load extension: %s", extension)

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
