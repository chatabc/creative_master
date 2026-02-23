"""
Creative Generator Module
Generates creative ideas based on inspiration combinations
"""

from typing import List, Dict, Optional
from ..models import Inspiration, InspirationCombination, Creative, AIModelConfig, UserFeedback


class CreativeGenerator:
    def __init__(self, config: Optional[AIModelConfig] = None):
        self.config = config
    
    def _build_context(
        self, 
        inspirations: List[Inspiration], 
        combination: InspirationCombination
    ) -> str:
        context_parts = []
        
        relation_map = {}
        for relation in combination.relations:
            key = (relation.source_id, relation.target_id)
            relation_map[key] = relation
        
        for i, inspiration in enumerate(inspirations):
            context_parts.append(f"\n### 灵感 {i+1}: {inspiration.name}")
            type_str = inspiration.type.value if hasattr(inspiration.type, 'value') else str(inspiration.type)
            context_parts.append(f"类型: {type_str}")
            
            if inspiration.summary:
                context_parts.append(f"内容摘要:\n{inspiration.summary}")
            
            for other in inspirations:
                if other.id != inspiration.id:
                    key = (inspiration.id, other.id)
                    if key in relation_map:
                        rel = relation_map[key]
                        rel_type_str = rel.relation_type.value if hasattr(rel.relation_type, 'value') else str(rel.relation_type)
                        context_parts.append(
                            f"与 '{other.name}' 的关系: {rel_type_str}"
                            + (f" - {rel.description}" if rel.description else "")
                        )
        
        return "\n".join(context_parts)
    
    async def generate_creatives(
        self,
        inspirations: List[Inspiration],
        combination: InspirationCombination,
        count: int = 3
    ) -> List[Creative]:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        context = self._build_context(inspirations, combination)
        
        response = await client.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {
                    "role": "system",
                    "content": """你是一个创意专家，擅长将不同的灵感元素组合成创新的创意方案。
请根据提供的灵感内容，生成多个独特、可行的创意方案。

每个创意方案需要包含：
1. 标题：简洁有吸引力的名称
2. 描述：详细的创意描述（200-300字）
3. 关键点：3-5个核心要点

请以JSON数组格式返回，格式如下：
[
  {
    "title": "创意标题",
    "description": "详细描述...",
    "key_points": ["要点1", "要点2", "要点3"]
  }
]"""
                },
                {
                    "role": "user",
                    "content": f"""灵感组合名称: {combination.name}

{context}

请基于以上灵感生成{count}个创意方案。注意：
- 充分考虑灵感之间的关系和主次
- 创意要新颖且具有可行性
- 每个创意应该有不同的方向和特点"""
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=3000
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        creatives = []
        
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            items = result.get("creatives", result.get("items", [result] if "title" in result else []))
        else:
            items = []
        
        for item in items:
            if isinstance(item, dict):
                creative = Creative(
                    combination_id=combination.id,
                    title=item.get("title", "未命名创意"),
                    description=item.get("description", ""),
                    key_points=item.get("key_points", [])
                )
                creatives.append(creative)
        
        return creatives[:count]
    
    async def regenerate_with_feedback(
        self,
        inspirations: List[Inspiration],
        combination: InspirationCombination,
        feedback: UserFeedback,
        count: int = 3
    ) -> List[Creative]:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        context = self._build_context(inspirations, combination)
        
        response = await client.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {
                    "role": "system",
                    "content": """你是一个创意专家，擅长根据用户反馈优化创意方案。
请根据用户的反馈意见，重新生成更符合需求的创意方案。

每个创意方案需要包含：
1. 标题：简洁有吸引力的名称
2. 描述：详细的创意描述（200-300字）
3. 关键点：3-5个核心要点

请以JSON数组格式返回。"""
                },
                {
                    "role": "user",
                    "content": f"""灵感组合名称: {combination.name}

{context}

用户反馈: {feedback.feedback}
{"用户评分: " + str(feedback.rating) + "/5" if feedback.rating else ""}

请根据用户反馈，重新生成{count}个更符合需求的创意方案。"""
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=3000
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        creatives = []
        
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            items = result.get("creatives", result.get("items", [result] if "title" in result else []))
        else:
            items = []
        
        for item in items:
            if isinstance(item, dict):
                creative = Creative(
                    combination_id=combination.id,
                    title=item.get("title", "未命名创意"),
                    description=item.get("description", ""),
                    key_points=item.get("key_points", [])
                )
                creatives.append(creative)
        
        return creatives[:count]
    
    async def score_creative(self, creative: Creative, criteria: Optional[Dict] = None) -> float:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        criteria_text = ""
        if criteria:
            criteria_text = "评分标准:\n" + "\n".join([f"- {k}: {v}" for k, v in criteria.items()])
        
        response = await client.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个创意评估专家，请对创意方案进行评分（0-10分）。只返回一个数字。"
                },
                {
                    "role": "user",
                    "content": f"""创意标题: {creative.title}
创意描述: {creative.description}
关键点: {', '.join(creative.key_points)}

{criteria_text}

请给出综合评分（0-10分），只返回数字。"""
                }
            ],
            max_tokens=10
        )
        
        try:
            return float(response.choices[0].message.content.strip())
        except ValueError:
            return 5.0
