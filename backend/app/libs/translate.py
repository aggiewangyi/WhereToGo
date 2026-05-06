"""
翻译服务 —— 通过 302.AI 代理调用 DeepL。
价格: 30 PTC / 百万字符
"""

import httpx

from app.core.config import get_settings

settings = get_settings()

_HEADERS = {
    "Authorization": f"Bearer {settings.API_302_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


async def translate_text(
    text: str | list[str],
    target_lang: str = "EN",
    source_lang: str | None = None,
) -> str | list[str]:
    """
    DeepL 翻译。
    302.AI endpoint: POST /deepl/v2/translate
    target_lang 支持: AR BG CS DA DE EL EN-GB EN-US ES ET FI FR HU ID IT JA KO
                      LT LV NB NL PL PT-BR PT-PT RO RU SK SL SV TR UK ZH ZH-HANS ZH-HANT
    """
    texts = [text] if isinstance(text, str) else text
    body: dict = {"text": texts, "target_lang": target_lang}
    if source_lang:
        body["source_lang"] = source_lang

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{settings.API_302_BASE_URL}/deepl/v2/translate",
            headers=_HEADERS,
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()

    translations = data.get("translations", [])
    results = [t.get("text", "") for t in translations]
    return results[0] if isinstance(text, str) else results
