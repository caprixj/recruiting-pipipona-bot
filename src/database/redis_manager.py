from redis.asyncio import Redis

from src.configs.env_settings import Settings


def get_redis_client(settings: Settings) -> Redis:
    """Creates an asynchronous Redis client based on provided settings.

    Args:
        settings (Settings): The application configuration object.

    Returns:
        Redis: An instance of redis.asyncio.Redis.
    """
    return Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,  # Ensures we get str instead of bytes
    )
