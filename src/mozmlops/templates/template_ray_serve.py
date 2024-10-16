# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# The original code in this file comes from the Ray serve documentation:
# https://docs.ray.io/en/latest/serve/develop-and-deploy.html#convert-a-model-into-a-ray-serve-application

from ray import serve

from fastapi import FastAPI
from pydantic import BaseModel, Field
from transformers import pipeline

app = FastAPI()


class TranslateRequest(BaseModel):
    text: str = Field(description="The text to translate")


@serve.deployment()
@serve.ingress(app)
class Translator:
    def __init__(self):
        # Load model
        self.model = pipeline("translation_en_to_fr", model="t5-small")

    @app.post("/")
    def translate(self, translate_request: TranslateRequest) -> str:
        # Run inference
        model_output = self.model(translate_request.text)

        # Post-process output to return only the translation text
        translation = model_output[0]["translation_text"]

        return translation


translator_app = Translator.bind()
