from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "WhereToGo Agent Tool"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # MySQL
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"
    DB_NAME: str = "wheretogo"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Alembic migrations use a synchronous driver."""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Redis
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # ---- 302.AI unified API gateway ----
    API_302_KEY: str = "API_302_KEY"
    API_302_BASE_URL: str = "https://api.302.ai"

    # LLM (via 302.AI, OpenAI-compatible)
    DEFAULT_MODEL: str = "gpt-4o"

    # ---- Agent 工具服务（对外 HTTP）----
    # 非空则要求请求头 X-Agent-API-Key 一致；生产务必配置
    AGENT_SERVICE_API_KEY: str = ""
    # 会话 / travel_memory 绑定的用户主键（须存在于 users 表，可建专用「服务用户」）
    AGENT_SERVICE_USER_ID: int = 1

    # Chat: 多智能体（意图→行程→行前）串联；False 时回退单 ReAct Agent
    CHAT_MULTI_AGENT: bool = True
    # 每轮对话后是否把满意/不满点合并进 users.travel_memory（额外一次小模型调用）
    CHAT_FEEDBACK_MEMORY: bool = True
    # LangGraph SqliteSaver 路径（空则使用 MemorySaver）；示例：./data/langgraph_ckpt.sqlite
    LANGGRAPH_SQLITE_PATH: str = ""
    # 单次工具调用超时（秒），超时返回「已跳过」文案，避免前端长时间无响应
    AGENT_TOOL_TIMEOUT_SEC: float = 45.0
    # ReAct 用 LLM 是否走 token 流式；False 可避免部分网关返回空 SSE 触发
    # ValueError: No generations found in stream
    CHAT_STREAM_LLM: bool = False
    # LLM 单次 HTTP 请求超时（秒）；防止 TLS 握手挂起导致重试延迟过长
    AGENT_LLM_TIMEOUT_SEC: float = 60.0
    # LLM 网络连接失败时的最大重试次数（指数退避：2s/4s/8s/16s）
    AGENT_LLM_RETRY: int = 5
    # 重试基础延迟（秒），实际延迟 = base * 2^(attempt-1)
    AGENT_LLM_RETRY_DELAY: float = 2.0

    # External services (all proxied through 302.AI)
    AMAP_API_KEY: str = ""       # 高德地图 (direct, not via 302)
    WEATHER_API_KEY: str = ""    # 和风天气 (direct, not via 302)

    model_config = {"env_file": ".env.example", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
