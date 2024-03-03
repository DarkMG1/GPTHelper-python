import os

import discord
from discord.ext import commands

from storage.confighelper import setup_config, get_config
from storage.databasehelper import setup_database
from util.gptapi import setup_openai

setup_config()
setup_database()


class GPTHelper(commands.Bot):
    GUILD = discord.Object(id=get_config().guild_id)

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name="OpenAI Completion"))

    def __init__(self, *, discord_intents: discord.Intents):
        super().__init__(
            owner_id=get_config().owner_id,
            command_prefix="!",
            help_command=None,
            intents=discord_intents)

    async def load_commands(self) -> None:
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/commands"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"commands.{extension}")
                    print(f"Loaded command {extension}")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    print(f"Failed to load command {extension}\n{exception}")

    async def load_events(self) -> None:
        for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/events"):
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"events.{extension}")
                    print(f"Loaded event {extension}")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    print(f"Failed to load event {extension}\n{exception}")

    async def setup_hook(self) -> None:
        print(f"Logged in as {self.user.name}")
        print("-------------------")
        await self.load_commands()
        await self.load_events()

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user or message.author.bot:
            return
        await self.process_commands(message)


intents = discord.Intents.default()
intents.guild_messages, intents.message_content, intents.reactions = True, True, True
client = GPTHelper(discord_intents=intents)

setup_openai()

client.run(get_config().discord_token)
