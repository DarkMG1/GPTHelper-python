import openai
import discord
import tiktoken

from discord import Message
from openai import AsyncOpenAI

from storage.classes import GPTMessage, GPTUser, GPTRequest, GPTChannel, GPTPrompt, GPTConversation, OpenAIResponse, OpenAIResult
from util.builder import geterrorembedbuilder
from storage.confighelper import get_config
from storage.databasehelper import add_request
from typing import Optional, List

def discord_message_to_message(message: Message) -> Optional[GPTMessage]:
    if (
        message.type == discord.MessageType.thread_starter_message
        and message.reference.cached_message
        and len(message.reference.cached_message.embeds) > 0
        and len(message.reference.cached_message.embeds[0].fields) > 0
    ):
        field = message.reference.cached_message.embeds[0].fields[0]
        if field.value:
            return GPTMessage(user=field.name, text=field.value)
    else:
        if message.content:
            return GPTMessage(user=message.author.name, text=message.content)
    return None

def split_into_shorter_messages(message: str) -> List[str]:
    return [
        message[i : i + 1700]
        for i in range(0, len(message), 1700)
    ]

api = AsyncOpenAI(
    api_key= get_config().openai_token,
    timeout= get_config().timeout
)

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
            prompt_tokens= response.usage.prompt_tokens,
            completion_tokens= response.usage.completion_tokens,
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
        embed =  geterrorembedbuilder("Thread Closed", "The thread has reached the model's context limit. Please restart the chat and ask the question again.")
    )
    await thread.edit(archived=True, locked=True)

def num_tokens_from_messages(messages: list[dict[str, str]], model):
    try:
        encoding = tiktoken.encoding_for_model(model.model_name)
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