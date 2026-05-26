import json
import re
import requests


def score_cases(
    case_text: str,
    indicator_name: str,
    indicator_desc: str,
    qca_type: str,
    api_key: str,
    model: str = "gpt-4o",
    base_url: str = "https://api.openai.com/v1",
    criteria_high: str = "",
    criteria_mid: str = "",
    criteria_low: str = "",
):
    """
    调用大模型对单个案例的单个理论指标进行评分。
    返回：(score, reasoning)
    - fsQCA：score ∈ {0.00, 0.25, 0.50, 0.75, 1.00}
    - csQCA：score ∈ {0, 1}
    """

    # ── 构建评价标准说明块 ────────────────────────────────
    criteria_block = ""
    if any([criteria_high.strip(), criteria_mid.strip(), criteria_low.strip()]):
        criteria_block = "\n\n## 评价标准（请严格依据以下标准判断）"
        if criteria_high.strip():
            criteria_block += f"\n- 高（得分 0.75 ~ 1.00）：{criteria_high}"
        if criteria_mid.strip():
            criteria_block += f"\n- 中（得分约 0.50）：{criteria_mid}"
        if criteria_low.strip():
            criteria_block += f"\n- 低（得分 0.00 ~ 0.25）：{criteria_low}"

    # ── 评分说明 ──────────────────────────────────────────
    if qca_type == "fsQCA":
        score_instruction = (
            "请给出 0.00 到 1.00 之间的任意连续小数得分，精确到两位小数。\n\n"
            "评分标准：\n"
            "- 0.00：完全不符合，文本字面内容完全没有该指标的任何体现\n"
            "- 0.10~0.40：基本不符合，文本有极少量或非常模糊的相关迹象\n"
            "- 0.50：仅在文本真正无法判断方向时使用，请尽量避免\n"
            "- 0.60~0.90：基本至明显符合，文本字面内容有清晰或较强的体现\n"
            "- 1.00：完全符合，文本字面内容明确且充分体现了该指标\n\n"
            "重要提示：\n"
            "- 只看文本字面意思，不要推测或延伸；\n"
            "- 有任何倾向性线索就据此判断，不要轻易给 0.50；\n"
            "- 模糊或不确定的内容应给低分而非中间值。"
        )
        score_field = "score（0.00~1.00 之间的任意连续小数，精确到两位小数）"
    else:
        score_instruction = (
            "请判断案例文本是否体现了该理论指标：\n"
            "- 0：不符合\n"
            "- 1：符合"
        )
        score_field = "score（取值必须是 0 或 1）"

    system_prompt = (
        "你是一位定性比较分析（QCA）领域的专业研究助理。\n"
        "你的任务是根据提供的理论指标定义和评价标准，对案例文本进行精确评分。\n"
        "评分原则：\n"
        "1. 严格根据文本内容的字面意思评分，不要过度推测或延伸理解。\n"
        "2. 字面内容与条件指标高度符合则给高分，模糊或不确定则给低分。\n"
        "3. 尽量避免给出 0.50 的临界值——只有在文本真正无法判断时才使用；"
        "如果文本有任何倾向性线索，请据此偏向高分或低分方向。\n"
        "4. 请严格按照要求的 JSON 格式返回结果，不要返回任何其他内容。"
    )

    user_prompt = (
        f"请对以下案例文本就指定理论指标进行 {qca_type} 评分。\n\n"
        f"## 理论指标\n"
        f"名称：{indicator_name}\n"
        f"说明：{indicator_desc if indicator_desc.strip() else '（未提供详细说明）'}"
        f"{criteria_block}\n\n"
        f"## 案例文本\n{case_text}\n\n"
        f"## 评分要求\n{score_instruction}\n\n"
        f"## 输出格式\n"
        f"请严格返回如下 JSON，不要有任何前缀或解释：\n"
        f'{{\n  "{score_field}": <数字>,\n'
        f'  "reasoning": "<100~200字的评分理由，说明案例文本中哪些内容支持了你的判断>"\n}}'
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 600
    }

    base_url = base_url.rstrip("/")
    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers, json=payload, timeout=60
    )

    if response.status_code != 200:
        raise RuntimeError(f"API 返回错误 {response.status_code}：{response.text[:200]}")

    content = response.json()["choices"][0]["message"]["content"].strip()
    content_clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()

    try:
        result = json.loads(content_clean)
    except json.JSONDecodeError:
        score_match  = re.search(r'"score[^"]*":\s*([\d.]+)', content_clean)
        reason_match = re.search(r'"reasoning":\s*"([^"]+)"', content_clean)
        score_val  = float(score_match.group(1))  if score_match  else None
        reason_val = reason_match.group(1)        if reason_match else content_clean[:200]
        return _normalize(score_val, qca_type), reason_val

    score_val = None
    for key in result:
        if "score" in key.lower():
            score_val = result[key]
            break
    reasoning_val = result.get("reasoning", "")

    return _normalize(score_val, qca_type), reasoning_val


def _normalize(score_val, qca_type):
    if score_val is None:
        return None
    try:
        score_val = float(score_val)
    except (ValueError, TypeError):
        return None
    if qca_type == "fsQCA":
        # 连续值，仅确保在 [0.00, 1.00] 范围内，保留两位小数
        return round(max(0.0, min(1.0, score_val)), 2)
    else:
        return 1 if score_val >= 0.5 else 0
