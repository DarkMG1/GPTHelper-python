from enum import Enum
from typing import List, Optional

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelInfo:
    model_name: str
    input_cost: float
    output_cost: float

@dataclass(frozen=True)
class Model(Enum):
    GPT_4_TURBO = ModelInfo("gpt-4-0125-preview", 0.01, 0.03)
    GPT_4_TURBO_VISION = ModelInfo("gpt-4-1106-vision-preview", 0.01, 0.03)
    GPT_3_5_TURBO = ModelInfo("gpt-3.5-turbo-0125", 0.0005, 0.0015)
    DALL_E_3 = ModelInfo("dall-e-3", 0.04, 0.08)

    def model_name(self) -> str:
        return self.value.model_name

    def input_cost(self) -> float:
        return self.value.input_cost

    def output_cost(self) -> float:
        return self.value.output_cost

@dataclass
class GPTChannel:
    id: int
    current_model: Model = Model.GPT_4_TURBO
    current_max_tokens: int = 4096
    current_temperature: float = 1.0

@dataclass
class GPTUser:
    id: int
    chats: int
    currently_chatting: bool
    gpt_channel: GPTChannel

@dataclass(frozen=True)
class GPTRequest:
    model: Model
    input_tokens: int
    output_tokens: int

@dataclass(frozen=True)
class GPTMessage:
    user: str
    text: Optional[str] = None

    def render(self):
        result = self.user + ":"
        if self.text is not None:
            result += " " + self.text
        return result

@dataclass
class GPTConversation:
    messages: List[GPTMessage]

    def prepend(self, message: GPTMessage):
        self.messages.insert(0, message)
        return self

    def render(self):
        return f"\n{"<|endoftext|>"}".join(
            [message.render() for message in self.messages]
        )

@dataclass(frozen=True)
class GPTPrompt:
    header: GPTMessage
    examples: List[GPTConversation]
    convo: GPTConversation

    def full_render(self, bot_name):
        messages = [
            {
                "role": "system",
                "content": self.render_system_prompt(),
            }
        ]
        for message in self.render_messages(bot_name):
            messages.append(message)
        return messages

    def render_system_prompt(self):
        return f"\n{"<|endoftext|>"}".join(
            [self.header.render()]
            + [GPTMessage("System", "Example conversations:").render()]
            + [
                GPTMessage(
                    "System", "Now, you will work with the actual current conversation."
                ).render()
            ]
        )

    def render_messages(self, bot_name):
        for message in self.convo.messages:
            if not bot_name in message.user:
                yield {
                    "role": "user",
                    "name": message.user,
                    "content": message.text,
                }
            else:
                yield {
                    "role": "assistant",
                    "name": bot_name,
                    "content": message.text,
                }

example_conversations : List[GPTConversation] = [
    GPTConversation(
        [
            GPTMessage("Lewis", "Hello!"),
            GPTMessage("GPTHelper",
                       "Hello. I am a bot which can help you answer any questions. Please ask a question."),
            GPTMessage("Lewis", "What is the capital of France?"),
            GPTMessage("GPTHelper", "The capital of France is Paris."),
        ]
    ),
    GPTConversation(
        [
            GPTMessage("Alice", "What is the weather like today?"),
            GPTMessage("GPTHelper", "The weather today is sunny."),
        ]
    ),
]
@dataclass(frozen=True)
class Configuration:
    discord_token: str = ""
    openai_token: str = ""
    instructions: str = "You are a tool that many people use. Your goal is to deliver information to the user in a way that is easy to understand. You are to deliver information as quickly as possible, without using filler words of any kind. You are a chatbot, and you are here to help. Try to make yourself undetectable by AI Detection tools."
    example_conversations: List[GPTConversation] = field(default_factory=lambda: example_conversations)
    owner_id: int =0
    guild_id: int = 0
    gptcategory_id: int = 0
    timeout: int = 120

class OpenAIResult(Enum):
    OK = 0
    TOO_LONG = 1
    INVALID_REQUEST = 2
    OTHER_ERROR = 3

@dataclass
class OpenAIResponse:
    status: OpenAIResult
    prompt_tokens: int
    completion_tokens: Optional[int]
    reply_text: Optional[str]
    status_text: Optional[str]

@dataclass
class QueueableList(list):
    def __init__(self, *args, callback=None):
        super().__init__(*args)
        self.callback = callback

    def append(self, item):
        super().append(item)
        if self.callback:
            self.callback()

    def extend(self, iterable):
        super().extend(iterable)
        if self.callback:
            self.callback()

    def insert(self, index, item):
        super().insert(index, item)
        if self.callback:
            self.callback()

    def remove(self, item):
        super().remove(item)
        if self.callback:
            self.callback()

    def pop(self, index=-1):
        item = super().pop(index)
        if self.callback:
            self.callback()
        return item

    def __delitem__(self, index):
        super().__delitem__(index)
        if self.callback:
            self.callback()

    def __setitem__(self, index, item):
        super().__setitem__(index, item)
        if self.callback:
            self.callback()

@dataclass
class QueueableDict(dict):
    def __init__(self, *args, callback=None, **kwargs):
        self.callback = callback
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.callback:
            self.callback()

    def __delitem__(self, key):
        super().__delitem__(key)
        if self.callback:
            self.callback()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        if self.callback:
            self.callback()