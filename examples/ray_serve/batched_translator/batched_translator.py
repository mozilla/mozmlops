# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# The original code in this file comes from the Ray serve documentation:
# https://docs.ray.io/en/latest/serve/develop-and-deploy.html#convert-a-model-into-a-ray-serve-application

from ray import serve
from ray.serve import Application

from fastapi import FastAPI
from pydantic import BaseModel, Field
from transformers import pipeline
from typing import List, Dict, Any

app = FastAPI()


class BatchedTranslatorArgs(BaseModel):
    task: str = Field(
        description="The task parameter of the transformers.TranslationPipeline"
    )
    model: str = Field(
        description="The model parameter of the transformers.TranslationPipeline"
    )


class TranslateRequest(BaseModel):
    text: str = Field(description="The text to translate")


@serve.deployment()
@serve.ingress(app)
class BatchedTranslator:
    def __init__(self, task: str, model: str):
        # Load model
        self.model = pipeline(task, model)

    # `batch_wait_timeout_s`: Controls how long Serve should wait for a batch once the first request arrives.
    # `max_batch_size`      : Controls the size of the batch. Once the first request arrives, @serve.batch decorator will wait for a
    #                         full batch (up to `max_batch_size`) until `batch_wait_timeout_s` is reached. If the timeout is reached,
    #                         the batch will be processed regardless of the batch size.
    # check out https://docs.ray.io/en/latest/serve/advanced-guides/dyn-req-batch.html#tips-for-fine-tuning-batching-parameters for
    # tips to fine-tune batching parameters
    @serve.batch(max_batch_size=4, batch_wait_timeout_s=0.1)
    async def _batched_translate_handler(self, inputs: List[str]) -> List[str]:
        print("Our input array has length:", len(inputs), inputs)

        # Run inference
        model_outputs = self.model(inputs)
        print("model_outputs:", model_outputs)

        # Post-process output to return only the translation text
        translations = [
            model_output["translation_text"] for model_output in model_outputs
        ]
        print("translations:", translations)

        return translations

    @app.post("/")
    async def translate(self, translate_request: TranslateRequest) -> str:
        result = await self._batched_translate_handler(translate_request.text)
        print("result:", result)
        return result

    # This function allows dynamically changing parameters without restarting replicas
    # https://docs.ray.io/en/latest/serve/production-guide/config.html#dynamically-change-parameters-without-restarting-replicas-user-config
    def reconfigure(self, user_config: Dict[str, Any]):
        self._batched_translate_handler.set_max_batch_size(
            user_config["max_batch_size"]
        )
        self._batched_translate_handler.set_batch_wait_timeout_s(
            user_config["batch_wait_timeout_s"]
        )


# Ray Serve Application builder
def batched_translator_app_builder(args: BatchedTranslatorArgs) -> Application:
    return BatchedTranslator.bind(args.task, args.model)


# IFF you want to auto-generate Serve config file (using `serve build` command) then uncomment the next statement, auto-generate the Serve config
# file and then comment it back again. Please note that the Serve config file for this app is already generated. If you are only running this app
# following the README then you don't need to change anything here.
# batched_translator_app = BatchedTranslator.bind()
