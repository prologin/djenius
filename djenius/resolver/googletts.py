import os
import aiohttp
from typing import AsyncGenerator

from djenius.resolver import Resolver, SearchResults

API_KEY = os.environ["GOOGLETTS_API_KEY"]


class GoogleTTS(Resolver):
    async def setup(self):
        self.session = aiohttp.ClientSession(headers={"X-Goog-Api-Key": API_KEY})

    async def cleanup(self):
        await self.session.close()

    async def search(self, query: str, limit: int) -> SearchResults:
        raise StopAsyncIteration()

    async def download(self, id: str) -> AsyncGenerator[None, bytes]:
        # ssml = " <speak> <break time='1s'/> <prosody rate='slow'> est-ce que tu veux du <emphasis level='strong'>caca</emphasis> kaki ? <p><s>suce mon cul.</s><s>bite dans fesse.</s></p> moi j'aime le SSML, pas toi ? </prosody> </speak>  "},
        langs = {}
        ssml = ""
        data = {
            "input": {
                "ssml": ssml,
                "voice": {
                    "languageCode": "fr-FR",
                    "name": "fr-FR-Wavenet-B",
                    "ssmlGender": "NEUTRAL",
                },
                "audioConfig": {"audioEncoding": "OGG_OPUS"},
            }
        }
        async with self.session.post(
            "https://texttospeech.googleapis.com/v1beta1/text:synthesize", json=data
        ) as response:
            pass
