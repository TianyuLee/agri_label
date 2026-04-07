# https://app.ofox.ai/dashboard
# token = "sk-of-jXZiCTXQPcuQPvwNPkXqKsIETHIfWzlgsnYnvcTPuNAgEpCXamVsiywlrQEDGWcd"


from openai import OpenAI

client = OpenAI(
    api_key="sk-of-jXZiCTXQPcuQPvwNPkXqKsIETHIfWzlgsnYnvcTPuNAgEpCXamVsiywlrQEDGWcd",
    base_url="https://api.ofox.ai/v1",
)

response = client.chat.completions.create(
    model="openai/gpt-5.2",
    messages=[{"role": "user", "content": "关于柑橘得了黄龙病怎么指标这个问题，生成评价答案的rubric"}],
)
print(response.choices[0].message.content)