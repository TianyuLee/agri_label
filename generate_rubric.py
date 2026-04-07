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
        response = self.client.chat.completions.create(
            model="openai/gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content
        return content
    
def generate_rubric_answer_for_one_example(user_name, collection_name, prompt):
    gpt = GPT()
    instruction = generate_rubric_prompt.replace("<<<query>>>", prompt)
    response = gpt.invoke(instruction)
    match = re.findall(r"```json(.*?)```", response, flags=re.DOTALL)

    rubrics = []
    if match:
        json_str = match[-1]
        json_obj = json.loads(json_str)
        for obj in json_obj:
            rubrics.append({
                "criterion": obj['criterion'],
                "axis": "",
                "point": obj['point']
            })
    
    answers = []
    response = gpt.invoke(prompt)
    answers.append(response)

    output = {
        "user_name": user_name,
        "collection_name": collection_name,
        "prompt": prompt,
        "rubrics": rubrics,
        "answers": answers
    }
    return output

if __name__=='__main__':
    import re
    import json
    import pandas as pd


    output = []
    
    prompts = [
        "柑橘得了黄龙病怎么治疗",
        "柑桔遭遇寒潮怎么办？",
        "大棚辣椒施用了含缩二脲复合肥幼苗有烧苗现象如何解救？",
        "苹果得了炭疽病如何治疗？",
        "草莓得了炭疽病如何治疗？",
        "黄瓜得了白粉病要怎么治疗",
        "葡萄得了白粉病要怎么治疗",
        "玉米种植施肥要点",
        "大豆种植施肥要点",
        "菠菜种植施肥要点"
    ]
    for prompt in prompts:
        item = generate_rubric_answer_for_one_example(user_name="18222611632", collection_name="20260407", prompt=prompt)
        output.append(item)
    # item1 = generate_rubric_answer_for_one_example(user_name="18222611632", collection_name="20260407", prompt="柑橘得了黄龙病怎么治疗")
    # output.append(item1)

    # item2 = generate_rubric_answer_for_one_example(user_name="18222611632", collection_name="20260407", prompt="柑桔遭遇寒潮怎么办？")
    # output.append(item2)

    # item3 = generate_rubric_answer_for_one_example(user_name="18222611632", collection_name="20260407", prompt="大棚辣椒施用了含缩二脲复合肥幼苗有烧苗现象如何解救？")
    # output.append(item3)

    with open("rubric_output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
