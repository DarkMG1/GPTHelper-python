import os
import discord
from discord import Message as DiscordMessage, app_commands

from data import load_gpt_users, load_configuration, load_requests_map

gpt_users, configuration, requests_map = load_gpt_users(), load_configuration(), load_requests_map()

if (configuration.discord_token == "" or
        configuration.openai_token == "" or
        configuration.guildid == 0 or
        configuration.gptcategoryid == 0 or
        configuration.timeout == 0):
    print("Please fill in the configuration file.")
    exit(0)

GUILD = discord.Object(id=configuration.guildid)


class GPTHelper(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}')

    def __init__(self, *, discord_intents: discord.Intents):
        super().__init__(intents=discord_intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)


intents = discord.Intents.default()
intents.guild_messages, intents.message_content, intents.reactions = True, True, True
client = GPTHelper(discord_intents=intents)

@client.tree.command()
@app_commands.describe(
    user="The user to setup"
)
@app_commands.
async def setup(interaction: discord.Interaction, user: discord.Member):
    """Set up a user with a channel to use the bot"""

client.run(configuration.discord_token)
