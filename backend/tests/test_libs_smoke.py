"""
Optional smoke tests for libs (call real APIs). Skip when env keys missing.

Run: poetry run pytest tests/test_libs_smoke.py -v
"""

import os

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.skipif(not os.getenv("API_302_KEY"), reason="API_302_KEY not set")
async def test_web_search_returns_list():
    from app.libs.search import web_search

    out = await web_search("厦门旅游攻略", num_results=2)
    assert isinstance(out, list)


@pytest.mark.skipif(not os.getenv("API_302_KEY"), reason="API_302_KEY not set")
async def test_translate_short_text():
    from app.libs.translate import translate_text

    out = await translate_text("你好", target_lang="EN")
    assert isinstance(out, str)
    assert len(out) > 0


@pytest.mark.skipif(not os.getenv("AMAP_API_KEY"), reason="AMAP_API_KEY not set")
async def test_geocode_amap():
    from app.libs.maps import geocode

    data = await geocode("北京市天安门")
    assert isinstance(data, dict)
    assert data.get("status") == "1" or "geocodes" in data


@pytest.mark.skipif(not os.getenv("WEATHER_API_KEY"), reason="WEATHER_API_KEY not set")
async def test_weather_now():
    from app.libs.weather import get_current_weather

    data = await get_current_weather("101010100")
    assert isinstance(data, dict)
