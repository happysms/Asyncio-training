# async with

from contextlib import asynccontextmanager
import aiohttp


async def download_webpage(url):
    with aiohttp.request.get(url) as r:
        pass


@asynccontextmanager
async def web_page(url):
    data = await download_webpage(url)
    yield data
    await update_stats(url)


async with web_page('google.com') as data:
    proccess(data)

