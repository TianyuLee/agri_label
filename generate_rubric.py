# https://app.ofox.ai/dashboard
# token = "sk-of-jXZiCTXQPcuQPvwNPkXqKsIETHIfWzlgsnYnvcTPuNAgEpCXamVsiywlrQEDGWcd"

from openai import OpenAI
generate_rubric_prompt = """
你是一个农业专家，帮我生成评价用户问题的rubrics。
rubrics的格式:
```
[
    {
        "criterion": "criterion 描述",
        "point": "分数 整数",
    },
    ...
]
```
备注:
criterion: describing attributes of a response to that particular conversation that should be rewarded or penalized. Rubric criteria
can range from specific facts that should be mentioned in the response (e.g., what medications to take and
at what dosage) to other aspects of desired behavior (e.g., asking the user to give more details about their
knee pain in order to pinpoint a more specific diagnosis). 生成时需要中文的criterion

point: 该条rubric的分数，满足得point分数，不满足得0分。反应rubric的重要程度。point可以为负数，比如-10，比如满足了推荐了违禁药品，则得-10分


用户问题: <<<query>>>

现在开始生成
"""
class GPT(object):
    def __init__(self):
        
        self.client = OpenAI(
            api_key="sk-of-jXZiCTXQPcuQPvwNPkXqKsIETHIfWzlgsnYnvcTPuNAgEpCXamVsiywlrQEDGWcd",
            base_url="https://api.ofox.ai/v1",
        )

    def invoke(self, prompt):
        instruction = generate_rubric_prompt.replace("<<<query>>>", prompt)
        response = self.client.chat.completions.create(
            model="openai/gpt-5.2",
            messages=[{"role": "user", "content": instruction}],
        )
        content = response.choices[0].message.content
        return content
    

if __name__=='__main__':
    gpt = GPT()
    prompt = "关于柑橘得了黄龙病怎么指标这个问题，生成评价答案的rubric"
    print(gpt.invoke(prompt))
