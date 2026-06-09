from openai import OpenAI
import time

class LLM(object):
    def __init__(self, model_name):
        self.model_name = model_name
        self.client = OpenAI(
            api_key="sk-of-jXZiCTXQPcuQPvwNPkXqKsIETHIfWzlgsnYnvcTPuNAgEpCXamVsiywlrQEDGWcd",
            base_url="https://api.ofox.ai/v1",
        )

    def invoke(self, messages):
        for i in range(10):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    timeout=180,
                    max_tokens=30000
                )
                # content = completion.choices[0].message.content
                return completion
            except Exception as e:
                print(e)
                time.sleep(10)
                continue


llm = LLM(model_name="anthropic/claude-opus-4.7")

res = llm.invoke([{"role": "user", "content": "你好"}])
print(res)