import aiohttp
from discord.ext import commands

import discord

from storage.classes import GPTMessage
from util.utils import discord_message_to_message, generate_completion_response, process_response
from util.builder import geterrorembedbuilder
from storage.databasehelper import get_gpt_users


class Completer(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.bot.user or message.author.bot:
            return

        channel = message.channel
        if not isinstance(channel, discord.Thread):
            return

        # ignore threads not created by the bot
        thread = channel
        if thread.owner_id != self.bot.user.id:
            return

        # ignore threads that are archived locked or title is not what we want
        if thread.archived or thread.locked or not thread.name.startswith("GPT Chat -"):
            # ignore this thread
            return

        gpt_user = None
        for user in get_gpt_users():
            if user.id == message.author.id and user.gpt_channel.id == thread.parent.id:
                gpt_user = user
                break
        if gpt_user is None:
            return

        if message.content == "close chat" or message.content == "restart chat" or message.content == "stop chat":
            return

        message_count = 0

        async for _ in message.channel.history(limit=None):
            message_count +=1

        if message_count > 200:
            await thread.send(embed=
                              geterrorembedbuilder(
                                  "Too many messages",
                    "You have sent too many messages in this thread. Please restart the chat."))
            return


        # Maybe put a wait if user has more messages (later)
        gpt_channel = gpt_user.gpt_channel
        channel_messages = [
            discord_message_to_message(message) async for message in thread.history(limit=200)
        ]
        for attachment in message.attachments:
            if attachment.filename.endswith(".txt"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        if resp.status != 200:
                            await channel.send(f"Warning: Could not download file with name: {attachment.filename}")
                            continue
                        data = await resp.text()
                        channel_messages.append(GPTMessage(user=message.author.name, text=data))
            else:
                await channel.send("Sending file through Assistants API Beta. This may take a while.")

        channel_messages = [x for x in channel_messages if x is not None]
        channel_messages.reverse()

        # generate the response
        async with thread.typing():

            response_data = await generate_completion_response(
                messages=channel_messages,
                channel_config=gpt_channel,
            )

        await process_response(
            gpt_user=gpt_user, thread=thread, response_data=response_data
        )



async def setup(bot) -> None:
    await bot.add_cog(Completer(bot))