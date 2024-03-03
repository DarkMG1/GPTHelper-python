from typing import Optional, List

import discord
import openai
import tiktoken
from discord import Message as DiscordMessage
from openai.types.beta.thread_create_params import Message
from openai.types.beta.threads import ThreadMessage

from storage.classes import GPTMessage, GPTUser, GPTRequest, GPTChannel, GPTPrompt, GPTConversation, OpenAIResponse, \
    OpenAIResult
from storage.confighelper import get_config
from storage.databasehelper import add_request
from util.builder import geterrorembedbuilder
from util.gptapi import get_api


def discord_message_to_gptmessage(message: DiscordMessage) -> Optional[GPTMessage]:
    if message.content:
        return GPTMessage(user=message.author.name, text=message.content)
    return None


def gpt_message_to_openai_message(gpt_messages: List[GPTMessage]) -> List[Message]:
    messages: List[Message] = []
    for gptmessage in gpt_messages:
        messages.append(Message(content=gptmessage.text, role="user"))
    return messages


def split_into_shorter_messages(message: str) -> List[str]:
    return [
        message[i: i + 1700]
        for i in range(0, len(message), 1700)
    ]


async def generate_completion_response(messages: List[GPTMessage], channel_config: GPTChannel) -> OpenAIResponse:
    rendered = None
    try:
        prompt = GPTPrompt(
            header=GPTMessage(
                "system", f"Instructions for GPTHelper: {get_config().instructions}"
            ),
            examples=get_config().example_conversations,
            convo=GPTConversation(messages),
        )
        rendered = prompt.full_render("GPTHelper")
        api = await get_api()
        response = await api.chat.completions.create(
            model=channel_config.current_model.model_name(),
            messages=rendered,
            temperature=channel_config.current_temperature,
            top_p=1.0,
            max_tokens=channel_config.current_max_tokens,
            stop=["<|endoftext|>"],
        )
        reply = response.choices[0].message.content.strip()
        return OpenAIResponse(
            status=OpenAIResult.OK,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            reply_text=reply,
            status_text=None
        )
    except openai.BadRequestError as e:
        if "This model's maximum context length" in str(e):
            return OpenAIResponse(
                status=OpenAIResult.TOO_LONG,
                prompt_tokens=num_tokens_from_messages(rendered, channel_config.current_model),
                completion_tokens=None,
                reply_text=None,
                status_text=str(e)
            )
        else:
            print(e)
            return OpenAIResponse(
                status=OpenAIResult.INVALID_REQUEST,
                prompt_tokens=num_tokens_from_messages(rendered, channel_config.current_model),
                completion_tokens=None,
                reply_text=None,
                status_text=str(e),
            )
    except Exception as e:
        print(e)
        return OpenAIResponse(
            status=OpenAIResult.OTHER_ERROR,
            prompt_tokens=num_tokens_from_messages(rendered, channel_config.current_model),
            completion_tokens=None,
            reply_text=None,
            status_text=str(e)
        )


async def process_response(gpt_user: GPTUser, thread: discord.Thread, response_data: OpenAIResponse):
    status = response_data.status
    reply_text = response_data.reply_text
    status_text = response_data.status_text
    add_request(gpt_user, GPTRequest(
        input_tokens=response_data.prompt_tokens,
        output_tokens=response_data.completion_tokens or 0,
        model=gpt_user.gpt_channel.current_model,
    ))
    if status is OpenAIResult.OK:
        if not reply_text:
            await thread.send(
                embed=geterrorembedbuilder("Error", "No response from the model. Please try again.")
            )
        else:
            shorter_response = split_into_shorter_messages(reply_text)
            for r in shorter_response:
                await thread.send(r)
    elif status is OpenAIResult.TOO_LONG:
        await close_thread(thread)
    elif status is OpenAIResult.INVALID_REQUEST:
        await thread.send(
            embed=geterrorembedbuilder("Invalid Request", f"**Error** - {status_text}")
        )
    else:
        await thread.send(
            embed=geterrorembedbuilder("Error", f"**Error** - {status_text}")
        )


async def close_thread(thread: discord.Thread):
    await thread.send(
        embed=geterrorembedbuilder("Thread Closed",
                                   "The thread has reached the model's context limit. Please restart the chat and ask the question again.")
    )
    await thread.edit(archived=True, locked=True)


def num_tokens_from_messages(messages: list[dict[str, str]], model):
    try:
        encoding = tiktoken.encoding_for_model(model.model_name())
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    tokens_per_message = 3
    tokens_per_name = 1
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(text=value, allowed_special={'<|endoftext|>'}))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens


def num_tokens_from_list(messages: list[ThreadMessage], model):
    try:
        encoding = tiktoken.encoding_for_model(model.model_name())
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    tokens_per_message = 3
    num_tokens = 0
    for processed in messages:
        if processed.role == "assistant":
            num_tokens += tokens_per_message
            num_tokens += len(encoding.encode(text=processed.content[0].text.value))


def num_tokens_from_bytes(file_data: bytes, model):
    try:
        encoding = tiktoken.encoding_for_model(model.model_name())
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    try:
        string_data = file_data.decode('utf-8')
    except UnicodeDecodeError:
        try:
            string_data = file_data.decode('ISO-8859-1')
        except UnicodeDecodeError:
            string_data = file_data.decode('latin1', errors='ignore')

    return len(encoding.encode(text=string_data))


def num_tokens_from_string(file_data: str, model):
    try:
        encoding = tiktoken.encoding_for_model(model.model_name())
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text=file_data))
