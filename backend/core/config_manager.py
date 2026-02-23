"""
Configuration persistence manager for Creative Master
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4


def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class ConfigManager:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(base_dir, "data")
        
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.config_file = os.path.join(data_dir, "config.json")
        self.model_configs_file = os.path.join(data_dir, "model_configs.json")
        self.combinations_file = os.path.join(data_dir, "combinations.json")
        self.creatives_file = os.path.join(data_dir, "creatives.json")
        self.relation_types_file = os.path.join(data_dir, "relation_types.json")
        self.prompts_file = os.path.join(data_dir, "prompts.json")
        
        self._model_configs: Dict[str, Any] = {}
        self._combinations: Dict[str, Any] = {}
        self._creatives: Dict[str, Any] = {}
        self._relation_types: Dict[str, Any] = {}
        self._prompts: Dict[str, Any] = {}
        
        self._load_all()
    
    def _load_all(self):
        self._model_configs = self._load_json(self.model_configs_file, {})
        self._combinations = self._load_json(self.combinations_file, {})
        self._creatives = self._load_json(self.creatives_file, {})
        self._relation_types = self._load_json(self.relation_types_file, {})
        self._prompts = self._load_json(self.prompts_file, {})
    
    def _load_json(self, filepath: str, default: Any) -> Any:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                return default
        return default
    
    def _save_json(self, filepath: str, data: Any):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=json_serializer)
    
    # Model Configs
    def get_model_configs(self) -> List[Dict]:
        return list(self._model_configs.values())
    
    def get_model_config(self, model_id: str) -> Optional[Dict]:
        return self._model_configs.get(model_id)
    
    def save_model_config(self, config: Dict) -> Dict:
        if 'id' not in config or not config['id']:
            config['id'] = str(uuid4())
        config['created_at'] = datetime.now().isoformat()
        config['updated_at'] = datetime.now().isoformat()
        self._model_configs[config['id']] = config
        self._save_json(self.model_configs_file, self._model_configs)
        return config
    
    def update_model_config(self, model_id: str, updates: Dict) -> Optional[Dict]:
        if model_id not in self._model_configs:
            return None
        self._model_configs[model_id].update(updates)
        self._model_configs[model_id]['updated_at'] = datetime.now().isoformat()
        self._save_json(self.model_configs_file, self._model_configs)
        return self._model_configs[model_id]
    
    def delete_model_config(self, model_id: str) -> bool:
        if model_id in self._model_configs:
            del self._model_configs[model_id]
            self._save_json(self.model_configs_file, self._model_configs)
            return True
        return False
    
    def get_default_model_config(self) -> Optional[Dict]:
        for config in self._model_configs.values():
            if config.get('is_default'):
                return config
        if self._model_configs:
            return list(self._model_configs.values())[0]
        return None
    
    def get_relation_completer_config(self) -> Optional[Dict]:
        for config in self._model_configs.values():
            if config.get('is_relation_completer'):
                return config
        return self.get_default_model_config()
    
    def get_topology_generator_config(self) -> Optional[Dict]:
        for config in self._model_configs.values():
            if config.get('is_topology_generator'):
                return config
        return self.get_default_model_config()
    
    def get_inspiration_generator_config(self) -> Optional[Dict]:
        for config in self._model_configs.values():
            if config.get('is_inspiration_generator'):
                return config
        return self.get_default_model_config()
    
    def clear_relation_completer(self):
        for config in self._model_configs.values():
            config['is_relation_completer'] = False
        self._save_json(self.model_configs_file, self._model_configs)
    
    def clear_topology_generator(self):
        for config in self._model_configs.values():
            config['is_topology_generator'] = False
        self._save_json(self.model_configs_file, self._model_configs)
    
    def clear_inspiration_generator(self):
        for config in self._model_configs.values():
            config['is_inspiration_generator'] = False
        self._save_json(self.model_configs_file, self._model_configs)
    
    # Combinations
    def get_combinations(self) -> List[Dict]:
        return list(self._combinations.values())
    
    def get_combination(self, combination_id: str) -> Optional[Dict]:
        return self._combinations.get(combination_id)
    
    def save_combination(self, combination: Dict) -> Dict:
        if 'id' not in combination or not combination['id']:
            combination['id'] = str(uuid4())
        combination['created_at'] = datetime.now().isoformat()
        self._combinations[combination['id']] = combination
        self._save_json(self.combinations_file, self._combinations)
        return combination
    
    def update_combination(self, combination_id: str, updates: Dict) -> Optional[Dict]:
        if combination_id not in self._combinations:
            return None
        self._combinations[combination_id].update(updates)
        self._save_json(self.combinations_file, self._combinations)
        return self._combinations[combination_id]
    
    def delete_combination(self, combination_id: str) -> bool:
        if combination_id in self._combinations:
            del self._combinations[combination_id]
            self._save_json(self.combinations_file, self._combinations)
            return True
        return False
    
    # Creatives
    def get_creatives(self, combination_id: str = None) -> List[Dict]:
        creatives = list(self._creatives.values())
        if combination_id:
            creatives = [c for c in creatives if c.get('combination_id') == combination_id]
        return creatives
    
    def get_creative(self, creative_id: str) -> Optional[Dict]:
        return self._creatives.get(creative_id)
    
    def save_creative(self, creative: Dict) -> Dict:
        if 'id' not in creative or not creative['id']:
            creative['id'] = str(uuid4())
        if 'created_at' not in creative:
            creative['created_at'] = datetime.now().isoformat()
        creative['updated_at'] = datetime.now().isoformat()
        self._creatives[creative['id']] = creative
        self._save_json(self.creatives_file, self._creatives)
        return creative
    
    def save_creatives(self, creatives: List[Dict]) -> List[Dict]:
        saved = []
        for creative in creatives:
            saved.append(self.save_creative(creative))
        return saved
    
    def delete_creative(self, creative_id: str) -> bool:
        if creative_id in self._creatives:
            del self._creatives[creative_id]
            self._save_json(self.creatives_file, self._creatives)
            return True
        return False
    
    # Relation Types
    def get_relation_types(self) -> List[Dict]:
        return list(self._relation_types.values())
    
    def get_relation_type(self, type_id: str) -> Optional[Dict]:
        return self._relation_types.get(type_id)
    
    def save_relation_type(self, relation_type: Dict) -> Dict:
        if 'id' not in relation_type or not relation_type['id']:
            relation_type['id'] = str(uuid4())
        relation_type['created_at'] = datetime.now().isoformat()
        self._relation_types[relation_type['id']] = relation_type
        self._save_json(self.relation_types_file, self._relation_types)
        return relation_type
    
    def update_relation_type(self, type_id: str, updates: Dict) -> Optional[Dict]:
        if type_id not in self._relation_types:
            return None
        self._relation_types[type_id].update(updates)
        self._save_json(self.relation_types_file, self._relation_types)
        return self._relation_types[type_id]
    
    def delete_relation_type(self, type_id: str) -> bool:
        if type_id in self._relation_types:
            del self._relation_types[type_id]
            self._save_json(self.relation_types_file, self._relation_types)
            return True
        return False
    
    def init_default_relation_types(self, default_types: List[Dict]):
        if not self._relation_types:
            for rt in default_types:
                rt['id'] = str(uuid4())
                rt['created_at'] = datetime.now().isoformat()
                self._relation_types[rt['id']] = rt
            self._save_json(self.relation_types_file, self._relation_types)
    
    # Prompts
    def get_prompts(self, creative_id: str = None) -> List[Dict]:
        prompts = list(self._prompts.values())
        if creative_id:
            prompts = [p for p in prompts if p.get('creative_id') == creative_id]
        return prompts
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict]:
        return self._prompts.get(prompt_id)
    
    def save_prompt(self, prompt: Dict) -> Dict:
        if 'id' not in prompt or not prompt['id']:
            prompt['id'] = str(uuid4())
        prompt['created_at'] = datetime.now().isoformat()
        self._prompts[prompt['id']] = prompt
        self._save_json(self.prompts_file, self._prompts)
        return prompt
    
    def delete_prompt(self, prompt_id: str) -> bool:
        if prompt_id in self._prompts:
            del self._prompts[prompt_id]
            self._save_json(self.prompts_file, self._prompts)
            return True
        return False
