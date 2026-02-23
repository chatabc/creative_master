"""
Data models for Creative Master
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from uuid import uuid4


class InspirationType(str, Enum):
    IMAGE = "image"
    CODE = "code"
    TEXT = "text"
    VIDEO = "video"
    AUDIO = "audio"
    FOLDER = "folder"
    MODEL = "model"
    ENVIRONMENT = "environment"
    DATA = "data"
    CONFIG = "config"
    DOCUMENT = "document"
    NOTEBOOK = "notebook"
    SCRIPT = "script"
    STYLE = "style"
    MARKUP = "markup"
    ARCHIVE = "archive"
    FONT = "font"
    THREE_D = "3d"
    OTHER = "other"


class RelationType(str, Enum):
    PRIMARY = "primary"
    PARALLEL = "parallel"
    CONTRAST = "contrast"
    CUSTOM = "custom"


class CustomRelationType(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    display_name: str
    description: Optional[str] = None
    style: Dict = Field(default_factory=lambda: {
        "stroke": "#6b7280",
        "strokeWidth": 2
    })
    created_at: datetime = Field(default_factory=datetime.now)


class CustomFileType(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    display_name: str
    extensions: List[str] = Field(default_factory=list)
    icon: Optional[str] = None
    color: str = "#6b7280"
    description: Optional[str] = None
    text_mode: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Inspiration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: str
    path: str
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class InspirationRelation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    relation_type: RelationType
    custom_type_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class InspirationCombination(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    inspirations: List[str] = Field(default_factory=list)
    sub_combinations: List[str] = Field(default_factory=list)
    relations: List[InspirationRelation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Creative(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    combination_id: str
    title: str
    description: str
    key_points: List[str] = Field(default_factory=list)
    score: Optional[float] = None
    prompt: Optional[str] = None
    aggregated_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class GeneratedPrompt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    creative_id: str
    content: str
    files: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class AIModelConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    provider: str
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    file_types: List[str] = Field(default_factory=list)
    is_default: bool = False
    is_relation_completer: bool = False
    is_topology_generator: bool = False
    is_inspiration_generator: bool = False


class UserFeedback(BaseModel):
    creative_id: str
    feedback: str
    rating: Optional[int] = None


DEFAULT_FILE_TYPES: List[Dict] = [
    {
        "name": "image",
        "display_name": "图片",
        "extensions": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".ico", ".tiff", ".tif", ".heic", ".heif", ".raw", ".psd", ".ai", ".eps"],
        "icon": "image",
        "color": "#3b82f6",
        "description": "图片和设计文件",
        "text_mode": False
    },
    {
        "name": "code",
        "display_name": "代码",
        "extensions": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".hpp", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".vue", ".jsx", ".tsx", ".cs", ".scala", ".lua", ".r", ".m", ".mm", ".ex", ".exs", ".erl", ".clj", ".hs", ".ml", ".fs", ".dart", ".ktm", ".kts"],
        "icon": "code",
        "color": "#22c55e",
        "description": "编程代码文件",
        "text_mode": True
    },
    {
        "name": "text",
        "display_name": "文本",
        "extensions": [".txt", ".md", ".rst", ".log", ".csv", ".rtf", ".tex", ".org", ".adoc"],
        "icon": "file-text",
        "color": "#eab308",
        "description": "文本文件",
        "text_mode": True
    },
    {
        "name": "video",
        "display_name": "视频",
        "extensions": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg", ".3gp", ".ogv"],
        "icon": "video",
        "color": "#ef4444",
        "description": "视频文件",
        "text_mode": False
    },
    {
        "name": "audio",
        "display_name": "音频",
        "extensions": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus", ".aiff", ".ape", ".wv"],
        "icon": "music",
        "color": "#a855f7",
        "description": "音频文件",
        "text_mode": False
    },
    {
        "name": "model",
        "display_name": "模型文件",
        "extensions": [".pt", ".pth", ".h5", ".hdf5", ".onnx", ".pb", ".safetensors", ".bin", ".ckpt", ".pkl", ".pickle", ".weights", ".model", ".tflite", ".mlmodel", ".coreml"],
        "icon": "brain",
        "color": "#f97316",
        "description": "机器学习模型文件",
        "text_mode": False
    },
    {
        "name": "environment",
        "display_name": "环境文件",
        "extensions": [".yaml", ".yml", ".toml", ".ini", ".env", ".cfg", ".conf", ".properties", ".editorconfig", ".prettierrc", ".eslintrc", ".babelrc"],
        "icon": "settings",
        "color": "#06b6d4",
        "description": "配置和环境文件",
        "text_mode": True
    },
    {
        "name": "data",
        "display_name": "数据文件",
        "extensions": [".json", ".xml", ".parquet", ".feather", ".h5", ".hdf5", ".sql", ".db", ".sqlite", ".csv", ".tsv", ".arrow", ".orc", ".avro", ".proto"],
        "icon": "database",
        "color": "#8b5cf6",
        "description": "数据文件",
        "text_mode": True
    },
    {
        "name": "document",
        "display_name": "文档",
        "extensions": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".pages", ".numbers", ".keynote"],
        "icon": "file",
        "color": "#ec4899",
        "description": "办公文档文件",
        "text_mode": False
    },
    {
        "name": "archive",
        "display_name": "压缩包",
        "extensions": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".zst", ".tgz", ".tbz2"],
        "icon": "archive",
        "color": "#64748b",
        "description": "压缩文件",
        "text_mode": False
    },
    {
        "name": "font",
        "display_name": "字体",
        "extensions": [".ttf", ".otf", ".woff", ".woff2", ".eot", ".ttc"],
        "icon": "type",
        "color": "#14b8a6",
        "description": "字体文件",
        "text_mode": False
    },
    {
        "name": "3d",
        "display_name": "3D模型",
        "extensions": [".obj", ".fbx", ".gltf", ".glb", ".stl", ".dae", ".blend", ".max", ".ma", ".mb", ".3ds", ".ply"],
        "icon": "box",
        "color": "#f59e0b",
        "description": "3D模型文件",
        "text_mode": False
    },
    {
        "name": "notebook",
        "display_name": "笔记本",
        "extensions": [".ipynb", ".rmd", ".qmd"],
        "icon": "book",
        "color": "#0ea5e9",
        "description": "Jupyter和R Markdown笔记本",
        "text_mode": True
    },
    {
        "name": "script",
        "display_name": "脚本",
        "extensions": [".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd", ".vbs", ".ahk"],
        "icon": "terminal",
        "color": "#84cc16",
        "description": "脚本文件",
        "text_mode": True
    },
    {
        "name": "style",
        "display_name": "样式",
        "extensions": [".css", ".scss", ".sass", ".less", ".styl"],
        "icon": "palette",
        "color": "#d946ef",
        "description": "样式表文件",
        "text_mode": True
    },
    {
        "name": "markup",
        "display_name": "标记语言",
        "extensions": [".html", ".htm", ".xml", ".xhtml", ".svg", ".xsl", ".xslt"],
        "icon": "code",
        "color": "#f43f5e",
        "description": "标记语言文件",
        "text_mode": True
    },
    {
        "name": "other",
        "display_name": "其他",
        "extensions": [],
        "icon": "file",
        "color": "#6b7280",
        "description": "其他类型文件",
        "text_mode": False
    }
]


DEFAULT_RELATION_TYPES: List[Dict] = [
    {
        "name": "primary",
        "display_name": "主从关系",
        "description": "主从/支持与被支持关系，用箭头表示方向",
        "style": {
            "stroke": "#8b5cf6",
            "strokeWidth": 2,
            "markerEnd": "arrow"
        }
    },
    {
        "name": "parallel",
        "display_name": "平行关系",
        "description": "平行关系，用连线表示",
        "style": {
            "stroke": "#22c55e",
            "strokeWidth": 2
        }
    },
    {
        "name": "contrast",
        "display_name": "对比关系",
        "description": "对比关系，用双箭头表示",
        "style": {
            "stroke": "#ef4444",
            "strokeWidth": 2,
            "markerEnd": "arrow",
            "markerStart": "arrow"
        }
    }
]
