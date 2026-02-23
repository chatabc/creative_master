"""
AI Summarizer Module
Summarizes content from various inspiration types using AI
"""

import base64
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

from ..models import Inspiration, InspirationType, AIModelConfig


TEXT_MODE_TYPES = [
    InspirationType.CODE, InspirationType.TEXT, InspirationType.ENVIRONMENT,
    InspirationType.DATA, InspirationType.DOCUMENT, InspirationType.NOTEBOOK,
    InspirationType.SCRIPT, InspirationType.STYLE, InspirationType.MARKUP,
    InspirationType.FOLDER, InspirationType.CONFIG
]


class BaseSummarizer(ABC):
    @abstractmethod
    async def summarize(self, content: Any, **kwargs) -> str:
        pass


class ImageSummarizer(BaseSummarizer):
    def __init__(self, config: AIModelConfig):
        self.config = config
    
    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    async def summarize(self, image_path: str, **kwargs) -> str:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        base64_image = self._encode_image(image_path)
        
        response = await client.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请详细描述这张图片的内容，包括：1. 主要元素和主题 2. 色彩和构图特点 3. 可能传达的情感或意境 4. 适合用于什么类型的创意项目"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        return response.choices[0].message.content


class DocumentSummarizer(BaseSummarizer):
    def __init__(self, config: AIModelConfig):
        self.config = config
    
    def _read_docx(self, file_path: str) -> str:
        try:
            from docx import Document
            doc = Document(file_path)
            content = []
            for para in doc.paragraphs:
                if para.text.strip():
                    content.append(para.text)
            for table in doc.tables:
                for row in table.rows:
                    row_text = ' | '.join(cell.text for cell in row.cells)
                    if row_text.strip():
                        content.append(row_text)
            return '\n'.join(content)
        except Exception as e:
            return f"[无法解析Word文档: {str(e)}]"
    
    def _read_pdf(self, file_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            content = []
            for page in reader.pages:
                text = page.extract_text()
                if text and text.strip():
                    content.append(text)
            return '\n'.join(content)
        except Exception as e:
            return f"[无法解析PDF文档: {str(e)}]"
    
    def _read_content(self, file_path: str) -> str:
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext == '.docx':
            return self._read_docx(file_path)
        elif ext == '.pdf':
            return self._read_pdf(file_path)
        elif path.is_file():
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception:
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                        try:
                            return content.decode('utf-8')
                        except UnicodeDecodeError:
                            return content.decode('latin-1', errors='ignore')
                except Exception:
                    return ""
        elif path.is_dir():
            content_parts = []
            
            tree_structure = self._get_folder_structure(path)
            content_parts.append(f"=== 文件夹结构 ===\n{tree_structure}\n")
            
            for ext in ['.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.vue', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.sh', '.bat', '.ps1', '.env', '.ini', '.cfg', '.toml']:
                for file_path in path.rglob(f'*{ext}'):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            relative_path = file_path.relative_to(path)
                            content_parts.append(f"=== {relative_path} ===\n{f.read()[:3000]}")
                    except Exception:
                        continue
            
            return "\n\n".join(content_parts[:15])
    
    def _get_folder_structure(self, folder_path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
        if current_depth >= max_depth:
            return ""
        
        structure_lines = []
        try:
            items = sorted(folder_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items[:50]:
                if item.name.startswith('.') or item.name in ['node_modules', '__pycache__', '.git', 'venv', 'build', 'dist', '.venv']:
                    continue
                indent = "  " * current_depth
                if item.is_dir():
                    structure_lines.append(f"{indent}+ {item.name}/")
                    sub_structure = self._get_folder_structure(item, prefix, max_depth, current_depth + 1)
                    if sub_structure:
                        structure_lines.append(sub_structure)
                else:
                    size = item.stat().st_size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f}KB"
                    else:
                        size_str = f"{size / (1024 * 1024):.1f}MB"
                    structure_lines.append(f"{indent}- {item.name} ({size_str})")
        except PermissionError:
            pass
        
        return "\n".join(structure_lines)
    
    async def summarize(self, file_path: str, file_type: str = "document", **kwargs) -> str:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        content = self._read_content(file_path)
        
        if not content:
            return "无法读取文件内容"
        
        if len(content) > 10000:
            content = content[:10000] + "\n... (内容已截断)"
        
        type_prompts = {
            "code": "你是一个代码分析专家，请分析代码并总结其功能、结构和特点。",
            "text": "你是一个文本分析专家，请提取文本的关键信息。",
            "document": "你是一个文档分析专家，请分析文档内容并提取关键信息。",
            "notebook": "你是一个Jupyter笔记本分析专家，请分析笔记本内容并总结。",
            "script": "你是一个脚本分析专家，请分析脚本功能和使用方法。",
            "style": "你是一个样式分析专家，请分析CSS/样式表的结构和设计特点。",
            "markup": "你是一个标记语言分析专家，请分析HTML/XML结构和内容。",
            "data": "你是一个数据分析专家，请分析数据文件的结构和内容。",
            "environment": "你是一个配置分析专家，请分析配置文件的内容和用途。",
            "config": "你是一个配置分析专家，请分析配置文件的内容和用途。",
            "folder": """你是一个项目分析专家，请分析文件夹内容并生成详细的项目结构总结。

请按照以下格式输出：

## 项目概览
[简要描述这个项目/文件夹的用途和主题]

## 目录结构
[分析目录结构的特点，如模块划分、层次结构等]

## 主要文件分析
[分析关键文件的功能和作用]

## 技术栈/文件类型
[识别使用的技术、语言或文件类型]

## 创意灵感点
[提取可用于创意生成的灵感点和特色]

## 潜在应用场景
[这个项目/素材可以用于什么样的创意项目]"""
        }
        
        system_prompt = type_prompts.get(file_type, "你是一个内容分析专家，请分析并总结内容。")
        
        user_prompt = f"请分析以下内容并总结：\n\n1. 主要内容和主题\n2. 关键信息和要点\n3. 结构和特点\n4. 可用于创意的灵感点\n\n内容：\n{content}"
        
        if file_type == "folder":
            user_prompt = f"请分析以下文件夹内容并生成详细的项目结构总结：\n\n{content}"
        
        max_tokens_value = 10000 if file_type == "folder" else 2000
        
        response = await client.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            max_tokens=max_tokens_value
        )
        
        return response.choices[0].message.content


class TextContentSummarizer(BaseSummarizer):
    def __init__(self, config: AIModelConfig):
        self.config = config
    
    def _read_content(self, file_path: str) -> str:
        path = Path(file_path)
        
        if path.is_file():
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            except Exception:
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                        try:
                            return content.decode('utf-8')
                        except UnicodeDecodeError:
                            return content.decode('latin-1', errors='ignore')
                except Exception:
                    return ""
        elif path.is_dir():
            content_parts = []
            
            tree_structure = self._get_folder_structure(path)
            content_parts.append(f"=== 文件夹结构 ===\n{tree_structure}\n")
            
            file_count = 0
            dir_count = 0
            file_type_counts = {}
            main_files = []
            
            for ext in ['.py', '.js', '.ts', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.vue', '.jsx', '.tsx', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.sh', '.bat', '.ps1', '.env', '.ini', '.cfg', '.toml']:
                for file_path in path.rglob(f'*{ext}'):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            relative_path = file_path.relative_to(path)
                            content = f.read()
                            if len(content) > 0:
                                file_count += 1
                                main_files.append(f"  - {relative_path}")
                    except Exception:
                        continue
            
            for ext in ['.txt', '.md', '.doc', '.docx', '.pdf', '.rst']:
                for file_path in path.rglob(f'*{ext}'):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            relative_path = file_path.relative_to(path)
                            content = f.read()
                            if len(content) > 0:
                                file_count += 1
                                main_files.append(f"  - {relative_path}")
                    except Exception:
                        continue
            
            for item in path.iterdir():
                if item.is_dir() and not item.name.startswith('.') and item.name not in ['node_modules', '__pycache__', '.git', 'venv', 'build', 'dist', '.venv']:
                    dir_count += 1
                    try:
                        sub_items = list(item.iterdir())[:5]
                        sub_names = [sub.name for sub in sub_items if not sub.name.startswith('.')]
                        if sub_names:
                            content_parts.append(f"  - {item.name}/ ({', '.join(sub_names[:3])}{'...' if len(sub_names) > 3 else ''})")
                    except PermissionError:
                        pass
            
            if main_files:
                content_parts.append(f"\n主要文件 ({len(main_files)} 个):")
                for f in main_files[:10]:
                    content_parts.append(f"  {f}")
                if len(main_files) > 10:
                    content_parts.append(f"  ... 还有 {len(main_files) - 10} 个文件")
            
            content_parts.append(f"\n总计: {file_count} 个文件, {dir_count} 个文件夹")
            
            return "\n".join(content_parts[:20])
        
        return ""
    
    async def summarize(self, file_path: str, file_type: str = "text", **kwargs) -> str:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        content = self._read_content(file_path)
        
        if not content:
            return "无法读取文件内容"
        
        if len(content) > 10000:
            content = content[:10000] + "\n... (内容已截断)"
        
        type_prompts = {
            "code": "你是一个代码分析专家，请分析代码并总结其功能、结构和特点。",
            "text": "你是一个文本分析专家，请提取文本的关键信息。",
            "document": "你是一个文档分析专家，请分析文档内容并提取关键信息。",
            "notebook": "你是一个Jupyter笔记本分析专家，请分析笔记本内容并总结。",
            "script": "你是一个脚本分析专家，请分析脚本功能和使用方法。",
            "style": "你是一个样式分析专家，请分析CSS/样式表的结构和设计特点。",
            "markup": "你是一个标记语言分析专家，请分析HTML/XML结构和内容。",
            "data": "你是一个数据分析专家，请分析数据文件的结构和内容。",
            "environment": "你是一个配置分析专家，请分析配置文件的内容和用途。",
            "config": "你是一个配置分析专家，请分析配置文件的内容和用途。",
            "folder": "你是一个项目分析专家，请分析文件夹内容并总结项目结构。"
        }
        
        system_prompt = type_prompts.get(file_type, "你是一个内容分析专家，请分析并总结内容。")
        
        response = await client.chat.completions.create(
            model=self.config.model_name,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"请分析以下内容并总结：\n\n1. 主要内容和主题\n2. 关键信息和要点\n3. 结构和特点\n4. 可用于创意的灵感点\n\n内容：\n{content}"
                }
            ],
            max_tokens=2000
        )
        
        return response.choices[0].message.content


class AISummarizer:
    def __init__(self):
        self.model_configs: Dict[str, AIModelConfig] = {}
        self.summarizers: Dict[str, BaseSummarizer] = {}
        self.default_config: Optional[AIModelConfig] = None
    
    def register_model(self, config: AIModelConfig):
        for file_type in config.file_types:
            self.model_configs[file_type] = config
            
            if file_type == "image":
                self.summarizers[file_type] = ImageSummarizer(config)
            elif file_type == "document":
                self.summarizers[file_type] = DocumentSummarizer(config)
            elif file_type in ["code", "text", "notebook", "script", "style", "markup", "data", "environment", "config", "folder"]:
                self.summarizers[file_type] = TextContentSummarizer(config)
        
        if config.is_default:
            self.default_config = config
    
    def get_summarizer(self, inspiration_type: str) -> Optional[BaseSummarizer]:
        return self.summarizers.get(inspiration_type)
    
    async def summarize_inspiration(self, inspiration: Inspiration) -> str:
        summarizer = self.get_summarizer(inspiration.type)
        
        if not summarizer:
            if self.default_config:
                summarizer = DocumentSummarizer(self.default_config)
            else:
                return f"暂不支持 {inspiration.type} 类型的内容总结，请先配置AI模型"
        
        try:
            if isinstance(summarizer, (TextContentSummarizer, DocumentSummarizer)):
                summary = await summarizer.summarize(inspiration.path, inspiration.type)
            else:
                summary = await summarizer.summarize(inspiration.path)
            return summary
        except Exception as e:
            return f"总结失败: {str(e)}"
    
    async def batch_summarize(self, inspirations: List[Inspiration]) -> Dict[str, str]:
        results = {}
        for inspiration in inspirations:
            results[inspiration.id] = await self.summarize_inspiration(inspiration)
        return results
