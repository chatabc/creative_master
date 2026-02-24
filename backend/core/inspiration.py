"""
Inspiration Storage and Management Module
"""

import os
import shutil
import json
import time
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import Inspiration


class InspirationManager:
    def __init__(self, storage_path: str = "./storage/inspirations", file_type_manager=None):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.storage_path / "metadata.json"
        self.file_type_manager = file_type_manager
        self._load_metadata()
    
    def _load_metadata(self):
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Failed to load metadata, creating new one. Error: {e}")
                self.metadata = {"inspirations": {}}
                self._save_metadata()
        else:
            self.metadata = {"inspirations": {}}
            self._save_metadata()
    
    def _save_metadata(self):
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} is not JSON serializable")
        
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2, default=json_serializer)
    
    def _detect_type(self, file_path: str) -> str:
        if self.file_type_manager:
            return self.file_type_manager.detect_type(file_path)
        
        ext = Path(file_path).suffix.lower()
        type_mapping = {
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
            '.webp': 'image', '.bmp': 'image', '.svg': 'image', '.ico': 'image',
            '.mp4': 'video', '.avi': 'video', '.mov': 'video', '.mkv': 'video',
            '.mp3': 'audio', '.wav': 'audio', '.flac': 'audio', '.aac': 'audio',
            '.py': 'code', '.js': 'code', '.ts': 'code', '.java': 'code',
            '.cpp': 'code', '.c': 'code', '.go': 'code', '.rs': 'code',
            '.txt': 'text', '.md': 'text', '.rst': 'text', '.log': 'text',
            '.pt': 'model', '.pth': 'model', '.h5': 'model', '.onnx': 'model',
            '.yaml': 'environment', '.yml': 'environment', '.toml': 'environment',
            '.json': 'data', '.xml': 'data', '.parquet': 'data',
            '.pdf': 'document', '.doc': 'document', '.docx': 'document',
            '.zip': 'archive', '.rar': 'archive', '.7z': 'archive',
        }
        return type_mapping.get(ext, 'other')
    
    def add_inspiration(
        self, 
        source_path: str, 
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        copy_file: bool = True,
        file_type: Optional[str] = None
    ) -> Inspiration:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source path not found: {source_path}")
        
        if file_type:
            inspiration_type = file_type
        else:
            inspiration_type = self._detect_type(source_path)
        
        if source.is_dir():
            inspiration_type = "folder"
        
        name = name or source.name
        
        if copy_file:
            dest_folder = self.storage_path / inspiration_type
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            if source.is_file():
                unique_name = f"{source.stem}_{int(time.time())}{source.suffix}"
                dest_path = dest_folder / unique_name
                shutil.copy2(source, dest_path)
                stored_path = str(dest_path)
            else:
                dest_path = dest_folder / name
                dest_path.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, dest_path, dirs_exist_ok=True)
                stored_path = str(dest_path)
        else:
            stored_path = str(source.absolute())
        
        inspiration = Inspiration(
            name=name,
            type=inspiration_type,
            path=stored_path,
            tags=tags or [],
            metadata={
                "original_path": str(source.absolute()),
                "size": self._get_size(stored_path),
                "extension": source.suffix.lower() if source.is_file() else None
            }
        )
        
        self.metadata["inspirations"][inspiration.id] = inspiration.model_dump()
        self._save_metadata()
        
        return inspiration
    
    def add_inspiration_from_upload(
        self,
        file_content: bytes,
        filename: str,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        file_type: Optional[str] = None
    ) -> Inspiration:
        temp_dir = Path(tempfile.gettempdir()) / "creative_master_uploads"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_path = temp_dir / f"{int(time.time())}_{filename}"
        with open(temp_path, 'wb') as f:
            f.write(file_content)
        
        try:
            inspiration = self.add_inspiration(
                source_path=str(temp_path),
                name=name or Path(filename).name,
                tags=tags,
                copy_file=True,
                file_type=file_type
            )
            return inspiration
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def _get_size(self, path: str) -> int:
        p = Path(path)
        if p.is_file():
            return p.stat().st_size
        return sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
    
    def get_inspiration(self, inspiration_id: str) -> Optional[Inspiration]:
        data = self.metadata["inspirations"].get(inspiration_id)
        if data:
            return Inspiration(**data)
        return None
    
    def list_inspirations(
        self, 
        type_filter: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Inspiration]:
        results = []
        for data in self.metadata["inspirations"].values():
            inspiration = Inspiration(**data)
            
            if type_filter and inspiration.type != type_filter:
                continue
            
            if tags and not any(tag in inspiration.tags for tag in tags):
                continue
            
            results.append(inspiration)
        
        return results
    
    def update_inspiration(
        self, 
        inspiration_id: str, 
        **updates
    ) -> Optional[Inspiration]:
        if inspiration_id not in self.metadata["inspirations"]:
            return None
        
        data = self.metadata["inspirations"][inspiration_id]
        data.update(updates)
        data["updated_at"] = datetime.now().isoformat()
        
        self.metadata["inspirations"][inspiration_id] = data
        self._save_metadata()
        
        return Inspiration(**data)
    
    def delete_inspiration(self, inspiration_id: str) -> bool:
        if inspiration_id not in self.metadata["inspirations"]:
            return False
        
        inspiration_data = self.metadata["inspirations"][inspiration_id]
        stored_path = Path(inspiration_data["path"])
        
        if stored_path.exists() and self.storage_path in stored_path.parents:
            if stored_path.is_dir():
                shutil.rmtree(stored_path)
            else:
                stored_path.unlink()
        
        del self.metadata["inspirations"][inspiration_id]
        self._save_metadata()
        
        return True
    
    def add_tags(self, inspiration_id: str, tags: List[str]) -> Optional[Inspiration]:
        inspiration = self.get_inspiration(inspiration_id)
        if not inspiration:
            return None
        
        new_tags = list(set(inspiration.tags + tags))
        return self.update_inspiration(inspiration_id, tags=new_tags)
    
    def search_inspirations(self, query: str) -> List[Inspiration]:
        results = []
        query_lower = query.lower()
        
        for data in self.metadata["inspirations"].values():
            if query_lower in data["name"].lower():
                results.append(Inspiration(**data))
            elif data.get("summary") and query_lower in data["summary"].lower():
                results.append(Inspiration(**data))
            elif any(query_lower in tag.lower() for tag in data.get("tags", [])):
                results.append(Inspiration(**data))
        
        return results
    
    def refresh_all_types(self, type_detector) -> int:
        updated_count = 0
        
        for inspiration_id, data in self.metadata["inspirations"].items():
            if data.get("type") == "folder":
                continue
            
            stored_path = data.get("path")
            if not stored_path:
                continue
            
            path = Path(stored_path)
            if not path.exists():
                continue
            
            new_type = type_detector(path)
            if new_type and new_type != data.get("type"):
                data["type"] = new_type
                data["updated_at"] = datetime.now().isoformat()
                self.metadata["inspirations"][inspiration_id] = data
                updated_count += 1
        
        if updated_count > 0:
            self._save_metadata()
        
        return updated_count
    
    def batch_add_inspirations(
        self,
        files: List[Dict[str, Any]],
        default_tags: Optional[List[str]] = None
    ) -> List[Inspiration]:
        results = []
        for file_info in files:
            try:
                if "content" in file_info:
                    inspiration = self.add_inspiration_from_upload(
                        file_content=file_info["content"],
                        filename=file_info["filename"],
                        name=file_info.get("name"),
                        tags=file_info.get("tags", default_tags),
                        file_type=file_info.get("type")
                    )
                else:
                    inspiration = self.add_inspiration(
                        source_path=file_info["path"],
                        name=file_info.get("name"),
                        tags=file_info.get("tags", default_tags),
                        copy_file=file_info.get("copy_file", True),
                        file_type=file_info.get("type")
                    )
                results.append(inspiration)
            except Exception as e:
                print(f"Failed to add inspiration: {e}")
        
        return results
