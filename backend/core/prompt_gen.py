"""
Prompt Generator Module
Generates detailed prompts based on selected creatives
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from ..models import Inspiration, Creative, GeneratedPrompt, AIModelConfig


class PromptGenerator:
    def __init__(self, config: Optional[AIModelConfig] = None):
        self.config = config
    
    async def generate_prompt(
        self,
        creative: Creative,
        inspirations: List[Inspiration],
        output_format: str = "detailed",
        organize_files: bool = False,
        output_folder: Optional[str] = None,
        aggregated_path: Optional[str] = None
    ) -> GeneratedPrompt:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        inspiration_context = self._build_inspiration_context(inspirations, aggregated_path)
        
        format_instructions = {
            "detailed": "生成一个详细、结构化的提示词，包含背景、目标、要求、约束等部分。",
            "concise": "生成一个简洁但完整的提示词，突出核心要求。",
            "step_by_step": "生成一个分步骤的提示词，包含执行步骤和注意事项。"
        }
        
        response = await client.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {
                    "role": "system",
                    "content": """你是一个提示词工程专家，擅长将创意方案转化为高质量的AI提示词。
生成的提示词应该：
1. 清晰明确地描述目标和要求
2. 包含必要的上下文信息
3. 结构化组织，便于理解
4. 可以直接用于其他AI工具
5. 如果提供了文件路径信息，在提示词中引用这些路径"""
                },
                {
                    "role": "user",
                    "content": f"""创意方案:
标题: {creative.title}
描述: {creative.description}
关键点: {', '.join(creative.key_points)}

相关灵感素材:
{inspiration_context}

{format_instructions.get(output_format, format_instructions['detailed'])}

请生成一个完整的提示词。如果提供了文件路径，请在提示词中引用这些文件的具体路径。"""
                }
            ],
            max_tokens=10000
        )
        
        prompt_content = response.choices[0].message.content
        
        files = []
        if organize_files and output_folder:
            files = self._organize_files(inspirations, output_folder, creative.title)
        
        generated_prompt = GeneratedPrompt(
            creative_id=creative.id,
            content=prompt_content,
            files=files
        )
        
        return generated_prompt
    
    def _build_inspiration_context(self, inspirations: List[Inspiration], aggregated_path: Optional[str] = None) -> str:
        parts = []
        for i, insp in enumerate(inspirations, 1):
            parts.append(f"\n### 灵感素材 {i}: {insp.name}")
            type_str = insp.type.value if hasattr(insp.type, 'value') else str(insp.type)
            parts.append(f"类型: {type_str}")
            if insp.summary:
                parts.append(f"内容: {insp.summary}")
            
            if aggregated_path:
                import os
                from pathlib import Path
                agg_path = Path(aggregated_path)
                if agg_path.exists():
                    type_folder = agg_path / type_str
                    if type_folder.exists():
                        parts.append(f"聚合后路径: {type_folder / Path(insp.path).name}")
                    else:
                        parts.append(f"聚合文件夹: {aggregated_path}")
                else:
                    parts.append(f"原始路径: {insp.path}")
            else:
                parts.append(f"原始路径: {insp.path}")
            
            file_structure = self._get_file_structure(insp.path)
            if file_structure:
                parts.append(f"文件结构:\n{file_structure}")
        
        return "\n".join(parts)
    
    def _get_file_structure(self, path: str, max_depth: int = 2, current_depth: int = 0) -> str:
        from pathlib import Path
        
        p = Path(path)
        if not p.exists():
            return ""
        
        if current_depth >= max_depth:
            return ""
        
        lines = []
        indent = "  " * current_depth
        
        if p.is_file():
            return f"{indent}- {p.name} (文件)"
        
        try:
            items = sorted(p.iterdir(), key=lambda x: (not x.is_file(), x.name))
            for item in items[:20]:
                if item.name.startswith('.'):
                    continue
                if item.is_file():
                    lines.append(f"{indent}- {item.name}")
                else:
                    lines.append(f"{indent}+ {item.name}/")
                    sub_structure = self._get_file_structure(str(item), max_depth, current_depth + 1)
                    if sub_structure:
                        lines.append(sub_structure)
        except PermissionError:
            pass
        
        return "\n".join(lines)
    
    def _organize_files(
        self, 
        inspirations: List[Inspiration], 
        output_folder: str,
        creative_name: str
    ) -> List[str]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in creative_name if c.isalnum() or c in (' ', '-', '_')).strip()
        folder_name = f"{safe_name}_{timestamp}"
        
        target_folder = Path(output_folder) / folder_name
        target_folder.mkdir(parents=True, exist_ok=True)
        
        copied_files = []
        
        for insp in inspirations:
            source = Path(insp.path)
            if not source.exists():
                continue
            
            dest = target_folder / insp.type.value / source.name
            
            if source.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                copied_files.append(str(dest))
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, dest, dirs_exist_ok=True)
                copied_files.append(str(dest))
        
        return copied_files
    
    async def generate_batch_prompts(
        self,
        creatives: List[Creative],
        inspirations_map: Dict[str, List[Inspiration]],
        output_format: str = "detailed"
    ) -> List[GeneratedPrompt]:
        prompts = []
        for creative in creatives:
            inspirations = inspirations_map.get(creative.id, [])
            prompt = await self.generate_prompt(
                creative=creative,
                inspirations=inspirations,
                output_format=output_format
            )
            prompts.append(prompt)
        return prompts
    
    def export_prompt(
        self,
        prompt: GeneratedPrompt,
        output_path: str,
        format: str = "markdown"
    ) -> str:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "markdown":
            content = self._to_markdown(prompt)
        elif format == "json":
            import json
            content = json.dumps(prompt.model_dump(), ensure_ascii=False, indent=2)
        else:
            content = prompt.content
        
        with open(output, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(output)
    
    def _to_markdown(self, prompt: GeneratedPrompt) -> str:
        lines = [
            "# 创意提示词",
            "",
            f"生成时间: {prompt.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 提示词内容",
            "",
            prompt.content,
        ]
        
        if prompt.files:
            lines.extend([
                "",
                "## 相关文件",
                ""
            ])
            for f in prompt.files:
                lines.append(f"- {f}")
        
        return "\n".join(lines)
