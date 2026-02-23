"""
File Type Manager Module
Manages custom file types and their extensions
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..models import CustomFileType, DEFAULT_FILE_TYPES


class ExtensionConflict:
    def __init__(self, extension: str, current_type: str, current_display_name: str):
        self.extension = extension
        self.current_type = current_type
        self.current_display_name = current_display_name
    
    def to_dict(self):
        return {
            "extension": self.extension,
            "current_type": self.current_type,
            "current_display_name": self.current_display_name
        }


class FileTypeManager:
    def __init__(self, storage_path: str = "./storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.config_path = self.storage_path / "file_types.json"
        self._load_config()
    
    def _load_config(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.file_types = [CustomFileType(**ft) for ft in data.get("file_types", [])]
            except (json.JSONDecodeError, Exception):
                self.file_types = [CustomFileType(**ft) for ft in DEFAULT_FILE_TYPES]
                self._save_config()
        else:
            self.file_types = [CustomFileType(**ft) for ft in DEFAULT_FILE_TYPES]
            self._save_config()
    
    def _save_config(self):
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, CustomFileType):
                return obj.model_dump()
            raise TypeError(f"Type {type(obj)} is not JSON serializable")
        
        data = {
            "file_types": [ft.model_dump() for ft in self.file_types],
            "updated_at": datetime.now().isoformat()
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=json_serializer)
    
    def list_file_types(self) -> List[CustomFileType]:
        return self.file_types
    
    def get_file_type(self, name: str) -> Optional[CustomFileType]:
        for ft in self.file_types:
            if ft.name == name:
                return ft
        return None
    
    def get_file_type_by_id(self, type_id: str) -> Optional[CustomFileType]:
        for ft in self.file_types:
            if ft.id == type_id:
                return ft
        return None
    
    def detect_type(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        
        if Path(file_path).is_dir():
            return "folder"
        
        for ft in self.file_types:
            if ext in ft.extensions:
                return ft.name
        
        return "other"
    
    def check_extension_conflicts(self, extensions: List[str]) -> List[Dict]:
        conflicts = []
        normalized_extensions = []
        
        for ext in extensions:
            normalized = ext.lower() if not ext.startswith('.') else ext.lower()
            normalized_extensions.append(normalized)
        
        for ext in normalized_extensions:
            for ft in self.file_types:
                if ext in ft.extensions:
                    conflicts.append(ExtensionConflict(
                        extension=ext,
                        current_type=ft.name,
                        current_display_name=ft.display_name
                    ))
                    break
        
        return [c.to_dict() for c in conflicts]
    
    def add_file_type(
        self,
        name: str,
        display_name: str,
        extensions: List[str],
        icon: Optional[str] = None,
        color: str = "#6b7280",
        description: Optional[str] = None,
        force_replace: bool = False,
        extensions_to_replace: Optional[List[str]] = None
    ) -> Tuple[CustomFileType, List[Dict]]:
        for ft in self.file_types:
            if ft.name == name:
                raise ValueError(f"文件类型 '{name}' 已存在")
        
        normalized_extensions = []
        for ext in extensions:
            normalized = ext.lower() if not ext.startswith('.') else ext.lower()
            normalized_extensions.append(normalized)
        
        conflicts = self.check_extension_conflicts(normalized_extensions)
        
        if conflicts and not force_replace:
            return None, conflicts
        
        if force_replace and extensions_to_replace:
            for ext in extensions_to_replace:
                ext_lower = ext.lower() if not ext.startswith('.') else ext.lower()
                for i, ft in enumerate(self.file_types):
                    if ext_lower in ft.extensions:
                        ft.extensions.remove(ext_lower)
                        ft.updated_at = datetime.now()
                        self.file_types[i] = ft
                        break
        
        file_type = CustomFileType(
            name=name,
            display_name=display_name,
            extensions=normalized_extensions,
            icon=icon,
            color=color,
            description=description
        )
        
        self.file_types.append(file_type)
        self._save_config()
        
        return file_type, []
    
    def update_file_type(
        self,
        type_id: str,
        display_name: Optional[str] = None,
        extensions: Optional[List[str]] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        description: Optional[str] = None,
        text_mode: Optional[bool] = None,
        force_replace: bool = False,
        extensions_to_replace: Optional[List[str]] = None
    ) -> Tuple[Optional[CustomFileType], List[Dict]]:
        target_index = None
        target_ft = None
        
        for i, ft in enumerate(self.file_types):
            if ft.id == type_id:
                target_index = i
                target_ft = ft
                break
        
        if target_ft is None:
            return None, []
        
        if extensions is not None:
            normalized_extensions = []
            for ext in extensions:
                normalized = ext.lower() if not ext.startswith('.') else ext.lower()
                normalized_extensions.append(normalized)
            
            conflicts = []
            for ext in normalized_extensions:
                for ft in self.file_types:
                    if ft.id != type_id and ext in ft.extensions:
                        conflicts.append({
                            "extension": ext,
                            "current_type": ft.name,
                            "current_display_name": ft.display_name
                        })
                        break
            
            if conflicts and not force_replace:
                return None, conflicts
            
            if force_replace and extensions_to_replace:
                for ext in extensions_to_replace:
                    ext_lower = ext.lower() if not ext.startswith('.') else ext.lower()
                    for i, ft in enumerate(self.file_types):
                        if ft.id != type_id and ext_lower in ft.extensions:
                            ft.extensions.remove(ext_lower)
                            ft.updated_at = datetime.now()
                            self.file_types[i] = ft
                            break
            
            target_ft.extensions = normalized_extensions
        
        if display_name is not None:
            target_ft.display_name = display_name
        if icon is not None:
            target_ft.icon = icon
        if color is not None:
            target_ft.color = color
        if description is not None:
            target_ft.description = description
        if text_mode is not None:
            target_ft.text_mode = text_mode
        target_ft.updated_at = datetime.now()
        
        self.file_types[target_index] = target_ft
        self._save_config()
        
        return target_ft, []
    
    def delete_file_type(self, type_id: str) -> bool:
        for i, ft in enumerate(self.file_types):
            if ft.id == type_id:
                if ft.name in ["other"]:
                    raise ValueError(f"无法删除系统文件类型 '{ft.name}'")
                del self.file_types[i]
                self._save_config()
                return True
        return False
    
    def add_extension_to_type(self, type_name: str, extension: str, force_replace: bool = False) -> Tuple[Optional[CustomFileType], Optional[Dict]]:
        ext = extension.lower() if not extension.startswith('.') else extension.lower()
        
        for ft in self.file_types:
            if ext in ft.extensions:
                if ft.name == type_name:
                    return ft, None
                if not force_replace:
                    return None, {
                        "extension": ext,
                        "current_type": ft.name,
                        "current_display_name": ft.display_name
                    }
                else:
                    ft.extensions.remove(ext)
                    ft.updated_at = datetime.now()
                    self._save_config()
                    break
        
        for i, ft in enumerate(self.file_types):
            if ft.name == type_name:
                ft.extensions.append(ext)
                ft.updated_at = datetime.now()
                self.file_types[i] = ft
                self._save_config()
                return ft, None
        
        return None, None
    
    def remove_extension_from_type(self, type_name: str, extension: str) -> Optional[CustomFileType]:
        ext = extension.lower() if not extension.startswith('.') else extension.lower()
        
        for i, ft in enumerate(self.file_types):
            if ft.name == type_name:
                if ext in ft.extensions:
                    ft.extensions.remove(ext)
                    ft.updated_at = datetime.now()
                    self.file_types[i] = ft
                    self._save_config()
                return ft
        
        return None
    
    def get_all_extensions(self) -> Dict[str, str]:
        result = {}
        for ft in self.file_types:
            for ext in ft.extensions:
                result[ext] = ft.name
        return result
    
    def reset_to_default(self):
        self.file_types = [CustomFileType(**ft) for ft in DEFAULT_FILE_TYPES]
        self._save_config()
        return self.file_types
