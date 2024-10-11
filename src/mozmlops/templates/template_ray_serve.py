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

'''
def app_builder(args: Dict[str, str]) -> Application:
    return Translator.bind(args)
'''
# TODO Uncomment the next line if attempting to autogenerate the config.
#app = MozPilot.bind(args={})

translator_app = Translator.bind()
