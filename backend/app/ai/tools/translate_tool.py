from langchain_core.tools import tool

from app.libs.translate import translate_text


@tool
async def translate(text: str, target_lang: str = "EN", source_lang: str | None = None) -> str:
    """
    使用 DeepL 翻译文本。
    target_lang 常用值: ZH(中文) EN(英文) JA(日文) KO(韩文) FR(法文) DE(德文) ES(西班牙文)
    用于帮助用户翻译菜单、路牌、常用语等旅行场景。
    """
    try:
        result = await translate_text(text, target_lang=target_lang, source_lang=source_lang)
        return result
    except Exception as e:
        return f"翻译失败: {e}"
