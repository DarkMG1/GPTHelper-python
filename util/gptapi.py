from openai import AsyncOpenAI

from storage.confighelper import get_config

api = None


def setup_openai():
    global api
    api = AsyncOpenAI(
        api_key=get_config().openai_token,
        timeout=get_config().timeout
    )


# noinspection PyTypeChecker
async def get_api() -> AsyncOpenAI:
    return api
