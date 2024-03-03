import asyncio
import tempfile

import aiohttp
import discord
import openai
from discord.ext import commands

from storage.classes import GPTMessage, RunResponse, RunResult, GPTRequest
from storage.confighelper import get_config
from storage.databasehelper import get_gpt_users, add_request
from util.builder import geterrorembedbuilder
from util.gptapi import get_api
from util.utils import discord_message_to_gptmessage, generate_completion_response, process_response, \
    split_into_shorter_messages, num_tokens_from_bytes, num_tokens_from_string, num_tokens_from_list


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
            message_count += 1

        if message_count > 200:
            await thread.send(embed=
            geterrorembedbuilder(
                "Too many messages",
                "You have sent too many messages in this thread. Please restart the chat."))
            return

        # Maybe put a wait if user has more messages (later)
        gpt_channel = gpt_user.gpt_channel
        channel_messages = [
            discord_message_to_gptmessage(message) async for message in thread.history(limit=200)
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

        channel_messages = [x for x in channel_messages if x is not None]
        channel_messages.reverse()

        for attachment in message.attachments:
            if not attachment.filename.endswith(".txt"):
                await channel.send(
                    "Sending file through Assistants API Beta. Currently, this does not support past context. This may take a while.")
                async with thread.typing():
                    api = await get_api()
                    assistant = await api.beta.assistants.create(
                        name=f'{message.author.name} - {gpt_user.chats}',
                        instructions=get_config().instructions,
                        tools=[{"type": "retrieval"}, {"type": "code_interpreter"}],
                        model=gpt_channel.current_model.model_name()
                    )
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            if resp.status != 200:
                                await channel.send(f"Warning: Could not download file with name: {attachment.filename}")
                                return
                            data = await resp.read()
                    with tempfile.NamedTemporaryFile(delete=True) as temp:
                        temp.write(data)
                        temp.flush()
                        temp.seek(0)
                        file_data = temp.read()
                    response = await api.files.create(file=file_data, purpose="assistants")
                    thread_o = await api.beta.threads.create(
                        messages=[
                            {
                                "role": "user",
                                "content": message.content if message.content else " ",
                                "file_ids": [response.id]
                            }
                        ]
                    )
                    run = await api.beta.threads.runs.create(
                        thread_id=thread_o.id,
                        assistant_id=assistant.id,
                    )
                    resp = await periodic_retrieval(api=api, thread_id=thread_o.id, run_id=run.id)
                    input_tokens = num_tokens_from_bytes(file_data, gpt_channel.current_model)
                    input_tokens += num_tokens_from_string(message.content, gpt_channel.current_model)
                    output_tokens = num_tokens_from_list(resp.messages.data, gpt_channel.current_model)
                    req = GPTRequest(
                        model=gpt_channel.current_model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens
                    )
                    add_request(user=gpt_user, request=req)
                    latest_resp = ""
                    for processed in resp.messages.data:
                        if processed.role == "assistant":
                            latest_resp = processed.content[0].text.value
                    if latest_resp == "":
                        await channel.send("There was no response from the Assistant.")
                    else:
                        shortened_resps = split_into_shorter_messages(latest_resp)
                        for resp in shortened_resps:
                            await channel.send(resp)
                    await api.beta.threads.delete(thread_o.id)
                    await api.files.delete(response.id)
                    await api.beta.assistants.delete(assistant.id)
                    return

        # generate the response
        async with thread.typing():

            response_data = await generate_completion_response(
                messages=channel_messages,
                channel_config=gpt_channel,
            )

        await process_response(
            gpt_user=gpt_user, thread=thread, response_data=response_data
        )


async def periodic_retrieval(api: openai.AsyncOpenAI, thread_id: str, run_id: str) -> RunResponse:
    while True:
        run = await api.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

        if run.status == "queued" or run.status == "in_progress":
            await asyncio.sleep(10)
            continue
        break
    messages = await api.beta.threads.messages.list(
        thread_id=thread_id,
        order="asc"
    )

    try:
        matched_status = RunResult[run.status.upper()]
    except KeyError:
        matched_status = RunResult.UNKNOWN

    return RunResponse(
        status=matched_status,
        messages=messages if messages else []
    )


async def setup(bot) -> None:
    await bot.add_cog(Completer(bot))
