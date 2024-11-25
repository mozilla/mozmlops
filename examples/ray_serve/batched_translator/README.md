# Example: Text Translator
**This is a text translator (English to French) Ray Serve app that demonstrates the [dynamic request batching](https://docs.ray.io/en/latest/serve/advanced-guides/dyn-req-batch.html#dynamic-request-batching) feature of Ray Serve. Dynamic batching can improve your service throughput without sacrificing latency. Batching is also necessary when your model is expensive to use and you want to maximize the utilization of hardware.**

### Details
- The app uses "t5-small" model from Hugging Face [transformers TranslationPipeline](https://huggingface.co/docs/transformers/en/main_classes/pipelines#transformers.TranslationPipeline) to translate text from English to French

#### Instructions to run locally
1. Create a python virtual environment to run the example and activate it
    ```sh
    python -m venv env_example_batched_translator
    source env_example_batched_translator/bin/activate
    ```
2. Install requirements from the [requirements.batched_translator.txt](./requirements.batched_translator.txt) file
    ```sh
    pip install -r requirements.batched_translator.txt
    ```
3. Run Ray Serve app using [serve run](https://docs.ray.io/en/latest/serve/api/index.html#serve-run) command

    > [!NOTE]
    > You can modify the [serve_config.yaml](./serve_config.yaml) file to set the [batching parameters](https://docs.ray.io/en/latest/serve/api/doc/ray.serve.batch.html#ray-serve-batch) `max_batch_size` and `batch_wait_timeout_s` as per your requirement

    ```sh
    serve run serve_config.yaml
    ```
4. Call the locally running service endpoint and check if it returns the expected response
   > [!NOTE]
   > You can either use the curl command given below to send a request (you can modify the text to be translated for each request) from separate terminal or you can go to http://127.0.0.1:8000/translate/docs in your browser and send a request via the interactive request console there.

    ```sh
    curl -i -d '{"text": "Hello world!"}' -X POST "http://127.0.0.1:8000/translate/" -H "Content-Type: application/json"
    ```
5. Once you are done, go to the terminal where `serve run` command was running and:
    1. Stop the Ray Serve app (kill the `serve run` process by Ctrl+C),
    2. Deactivate the virtual environment
        ```sh
        deactivate
        ```
