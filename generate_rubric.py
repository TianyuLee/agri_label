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

特别注意，当point为负数时，意味着criterion的描述也是负面的，比如"推荐了违禁药"，而不是"没有推荐违禁药"

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
    
def generate_rubric_answer_for_one_example(collection_name, prompt):
    for i in range(5):
        try:
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
                "collection_name": collection_name,
                "prompt": prompt,
                "rubrics": rubrics,
                "answers": answers
            }
            return output
        except Exception as e:
            print(e)
            import time
            time.sleep(5)
            continue

if __name__=='__main__':
    import re
    import json
    import pandas as pd


    output_path = "rubric_output_20260408.json"
    output = json.load(open(output_path, "r", encoding="utf-8"))
    cache = set([])
    for item in output:
        cache.add(item['prompt'])
    
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
    df = pd.read_excel("20260408_querys.xlsx")
    prompts = []
    for i,row in df.iterrows():
        prompts.append(row['问题'].strip())
    for prompt in prompts:
        assert prompt is not None and prompt != "" and isinstance(prompt, str)

    for i,prompt in enumerate(prompts):
        if prompt in cache:
            print(i, prompt, ' has processed')
            continue
        item = generate_rubric_answer_for_one_example(collection_name="20260407", prompt=prompt)
        output.append(item)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
        print(i, prompt)
    # item1 = generate_rubric_answer_for_one_example(collection_name="20260407", prompt="柑橘得了黄龙病怎么治疗")
    # output.append(item1)

    # item2 = generate_rubric_answer_for_one_example(collection_name="20260407", prompt="柑桔遭遇寒潮怎么办？")
    # output.append(item2)

    # item3 = generate_rubric_answer_for_one_example(collection_name="20260407", prompt="大棚辣椒施用了含缩二脲复合肥幼苗有烧苗现象如何解救？")
    # output.append(item3)


