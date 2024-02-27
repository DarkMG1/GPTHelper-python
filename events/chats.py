from discord.ext import commands

import discord
from util.builder import geterrorembedbuilder, getbaseembedbuilder
from storage.databasehelper import get_gpt_users


class Chats(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.bot.user or message.author.bot:
            return
        channel = message.channel
        thread = None
        is_thread = isinstance(channel, discord.Thread)
        if is_thread:
            thread = channel
            channel = channel.parent
        gpt_user = next(
            (user for user in get_gpt_users() if user.id == message.author.id and user.gpt_channel.id == channel.id),
            None)
        if gpt_user is None:
            return

        if message.content == "start chat":
            if gpt_user.currently_chatting:
                await channel.send(embed=geterrorembedbuilder("You have already started a chat", "You can only start one chat at a time"))
                return
            gpt_user.currently_chatting = True
            gpt_user.chats += 1
            thread = await message.channel.create_thread(
                name=f"GPT Chat - {message.author.name} - {gpt_user.chats}",
                reason="gpt-bot"
            )
            await thread.add_user(message.author)
            await message.reply("Created chat thread. You can now chat with the bot. Type `close chat` to close the chat.")
            return
        if not is_thread:
            return
        if thread.owner_id != self.bot.user.id or thread.archived or thread.locked or not thread.name.startswith("GPT Chat - "):
            return
        if message.content == "close chat" or message.content == "stop chat":
            gpt_user.currently_chatting = False
            await thread.send(
                embed = getbaseembedbuilder().settitle("Thread Closed").setdescription("The thread has been closed by the user.").black().build()
            )
            await thread.edit(archived=True, locked=True)
            return
        if message.content == "restart chat":
            await thread.edit(archived=True, locked=True)
            gpt_user.chats += 1
            await channel.create_thread(name=f"GPT Chat - {message.author.name} - {gpt_user.chats}")
            await thread.add_user(message.author)
            return
        pass

async def setup(bot) -> None:
    await bot.add_cog(Chats(bot))