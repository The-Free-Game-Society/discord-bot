import os
import logging

import discord
from discord import reaction
from discord.ext import commands, tasks

log = logging.getLogger("dummy_cog")


class DummyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


def setup(bot: commands.Bot):
    bot.add_cog(DummyCog(bot))
 