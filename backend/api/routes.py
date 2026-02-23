"""
API Routes for Creative Master
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from ..models import (
    Inspiration, InspirationCombination, 
    InspirationRelation, Creative, GeneratedPrompt, 
    AIModelConfig, UserFeedback, RelationType, CustomFileType, CustomRelationType,
    DEFAULT_RELATION_TYPES
)
from ..core import InspirationManager, AISummarizer, CreativeGenerator, PromptGenerator, FileTypeManager, ConfigManager


router = APIRouter()

config_manager = ConfigManager()
file_type_manager = FileTypeManager()
inspiration_manager = InspirationManager(file_type_manager=file_type_manager)
ai_summarizer = AISummarizer()
creative_generator = None
prompt_generator = None


def init_default_model():
    global creative_generator, prompt_generator
    default_config = config_manager.get_default_model_config()
    if default_config:
        config = AIModelConfig(**default_config)
        ai_summarizer.register_model(config)
        creative_generator = CreativeGenerator(config)
        prompt_generator = PromptGenerator(config)


init_default_model()


class AddInspirationRequest(BaseModel):
    source_path: str
    name: Optional[str] = None
    tags: Optional[List[str]] = None
    copy_file: bool = True
    file_type: Optional[str] = None


class CreateCombinationRequest(BaseModel):
    name: str
    description: Optional[str] = None
    inspiration_ids: List[str] = Field(default_factory=list)
    sub_combination_ids: List[str] = Field(default_factory=list)
    relations: Optional[List[InspirationRelation]] = None


class UpdateCombinationRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    inspiration_ids: Optional[List[str]] = None
    sub_combination_ids: Optional[List[str]] = None
    relations: Optional[List[InspirationRelation]] = None


class GenerateCreativesRequest(BaseModel):
    combination_id: str
    relations: Optional[List[InspirationRelation]] = None
    count: int = 3


class RegenerateRequest(BaseModel):
    combination_id: str
    feedback: str
    rating: Optional[int] = None
    count: int = 3


class GeneratePromptRequest(BaseModel):
    creative_id: str
    inspiration_ids: List[str]
    output_format: str = "detailed"
    organize_files: bool = False
    output_folder: Optional[str] = None


class ConfigModelRequest(BaseModel):
    name: str
    provider: str
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    file_types: List[str] = []
    is_default: bool = False
    is_relation_completer: bool = False
    is_topology_generator: bool = False
    is_inspiration_generator: bool = False


class AddFileTypeRequest(BaseModel):
    name: str
    display_name: str
    extensions: List[str]
    icon: Optional[str] = None
    color: str = "#6b7280"
    description: Optional[str] = None
    force_replace: bool = False
    extensions_to_replace: Optional[List[str]] = None


class UpdateFileTypeRequest(BaseModel):
    display_name: Optional[str] = None
    extensions: Optional[List[str]] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    text_mode: Optional[bool] = None
    force_replace: bool = False
    extensions_to_replace: Optional[List[str]] = None


class AddExtensionRequest(BaseModel):
    extension: str
    force_replace: bool = False


class CheckConflictsRequest(BaseModel):
    extensions: List[str]


class GenerateTopologyVariantsRequest(BaseModel):
    combination_id: str
    base_nodes: List[dict]
    base_edges: List[dict]
    base_relations: List[dict]


# ==================== File Types API ====================

@router.get("/file-types", response_model=List[CustomFileType])
async def list_file_types():
    return file_type_manager.list_file_types()


@router.get("/file-types/{type_name}", response_model=CustomFileType)
async def get_file_type(type_name: str):
    ft = file_type_manager.get_file_type(type_name)
    if not ft:
        raise HTTPException(status_code=404, detail="File type not found")
    return ft


@router.post("/file-types/check-conflicts")
async def check_extension_conflicts(request: CheckConflictsRequest):
    conflicts = file_type_manager.check_extension_conflicts(request.extensions)
    return {"conflicts": conflicts, "has_conflicts": len(conflicts) > 0}


@router.post("/file-types")
async def add_file_type(request: AddFileTypeRequest):
    try:
        file_type, conflicts = file_type_manager.add_file_type(
            name=request.name,
            display_name=request.display_name,
            extensions=request.extensions,
            icon=request.icon,
            color=request.color,
            description=request.description,
            force_replace=request.force_replace,
            extensions_to_replace=request.extensions_to_replace
        )
        
        if conflicts:
            return {
                "status": "conflict",
                "message": "以下后缀已存在于其他文件类型中",
                "conflicts": conflicts
            }
        
        return {"status": "success", "file_type": file_type.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/file-types/{type_id}")
async def update_file_type(type_id: str, request: UpdateFileTypeRequest):
    try:
        file_type, conflicts = file_type_manager.update_file_type(
            type_id=type_id,
            display_name=request.display_name,
            extensions=request.extensions,
            icon=request.icon,
            color=request.color,
            description=request.description,
            text_mode=request.text_mode,
            force_replace=request.force_replace,
            extensions_to_replace=request.extensions_to_replace
        )
        
        if not file_type:
            if conflicts:
                return {
                    "status": "conflict",
                    "message": "以下后缀已存在于其他文件类型中",
                    "conflicts": conflicts
                }
            raise HTTPException(status_code=404, detail="File type not found")
        
        return {"status": "success", "file_type": file_type.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/file-types/{type_id}")
async def delete_file_type(type_id: str):
    try:
        if not file_type_manager.delete_file_type(type_id):
            raise HTTPException(status_code=404, detail="File type not found")
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/file-types/{type_name}/extensions")
async def add_extension_to_type(type_name: str, request: AddExtensionRequest):
    try:
        ft, conflict = file_type_manager.add_extension_to_type(
            type_name, 
            request.extension,
            force_replace=request.force_replace
        )
        if not ft:
            if conflict:
                return {
                    "status": "conflict",
                    "message": f"后缀 '{conflict['extension']}' 已存在于 '{conflict['current_display_name']}' 中",
                    "conflict": conflict
                }
            raise HTTPException(status_code=404, detail="File type not found")
        return {"status": "success", "file_type": ft.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/file-types/{type_name}/extensions/{extension}")
async def remove_extension_from_type(type_name: str, extension: str):
    ft = file_type_manager.remove_extension_from_type(type_name, extension)
    if not ft:
        raise HTTPException(status_code=404, detail="File type not found")
    return ft


@router.post("/file-types/reset")
async def reset_file_types():
    return file_type_manager.reset_to_default()


# ==================== Inspirations API ====================

@router.post("/inspirations", response_model=Inspiration)
async def add_inspiration(request: AddInspirationRequest):
    try:
        inspiration = inspiration_manager.add_inspiration(
            source_path=request.source_path,
            name=request.name,
            tags=request.tags,
            copy_file=request.copy_file,
            file_type=request.file_type
        )
        return inspiration
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/inspirations/upload", response_model=Inspiration)
async def upload_inspiration(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    file_type: Optional[str] = Form(None)
):
    content = await file.read()
    
    inspiration = inspiration_manager.add_inspiration_from_upload(
        file_content=content,
        filename=file.filename or "unknown",
        name=name,
        tags=tags.split(",") if tags else [],
        file_type=file_type
    )
    return inspiration


@router.post("/inspirations/upload-batch", response_model=List[Inspiration])
async def upload_inspirations_batch(
    files: List[UploadFile] = File(...),
    tags: Optional[str] = Form(None),
    file_list: Optional[str] = Form(None)
):
    results = []
    
    if file_list:
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / "creative_master_folder_upload"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            temp_path = temp_dir / f"{int(time.time())}_folder.zip"
            with open(temp_path, 'wb') as f:
                f.write(await files[0].read())
            
            import zipfile
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir / "extracted")
            
            inspiration = inspiration_manager.add_inspiration(
                source_path=str(temp_dir / "extracted"),
                name=Path(files[0].filename).stem,
                tags=tags.split(",") if tags else [],
                copy_file=True
            )
            results.append(inspiration)
        finally:
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    else:
        for file in files:
            content = await file.read()
            inspiration = inspiration_manager.add_inspiration_from_upload(
                file_content=content,
                filename=file.filename or "unknown",
                tags=tags.split(",") if tags else []
            )
            results.append(inspiration)
    return results


@router.get("/inspirations", response_model=List[Inspiration])
async def list_inspirations(
    type: Optional[str] = None,
    tags: Optional[str] = None
):
    tag_list = tags.split(",") if tags else None
    return inspiration_manager.list_inspirations(type_filter=type, tags=tag_list)


@router.get("/inspirations/{inspiration_id}", response_model=Inspiration)
async def get_inspiration(inspiration_id: str):
    inspiration = inspiration_manager.get_inspiration(inspiration_id)
    if not inspiration:
        raise HTTPException(status_code=404, detail="Inspiration not found")
    return inspiration


@router.post("/inspirations/{inspiration_id}/summarize")
async def summarize_inspiration(inspiration_id: str, background_tasks: BackgroundTasks):
    inspiration = inspiration_manager.get_inspiration(inspiration_id)
    if not inspiration:
        raise HTTPException(status_code=404, detail="Inspiration not found")
    
    if not ai_summarizer.get_summarizer(inspiration.type):
        raise HTTPException(status_code=400, detail="No AI model configured for this type")
    
    summary = await ai_summarizer.summarize_inspiration(inspiration)
    inspiration_manager.update_inspiration(inspiration_id, summary=summary)
    
    return {"inspiration_id": inspiration_id, "summary": summary}


@router.delete("/inspirations/{inspiration_id}")
async def delete_inspiration(inspiration_id: str):
    if not inspiration_manager.delete_inspiration(inspiration_id):
        raise HTTPException(status_code=404, detail="Inspiration not found")
    return {"status": "deleted"}


class AICompleteRelationsRequest(BaseModel):
    inspiration_ids: List[str]
    existing_relations: Optional[List[Dict]] = None


@router.post("/inspirations/ai-complete-relations")
async def ai_complete_relations(request: AICompleteRelationsRequest):
    global ai_summarizer
    
    if not ai_summarizer or not ai_summarizer.default_config:
        raise HTTPException(status_code=400, detail="No AI model configured")
    
    inspirations = []
    for insp_id in request.inspiration_ids:
        insp = inspiration_manager.get_inspiration(insp_id)
        if insp:
            inspirations.append(insp)
    
    if len(inspirations) < 2:
        raise HTTPException(status_code=400, detail="At least 2 inspirations required")
    
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(
        api_key=ai_summarizer.default_config.api_key,
        base_url=ai_summarizer.default_config.base_url
    )
    
    insp_info = []
    for insp in inspirations:
        summary_preview = (insp.summary[:500] + "...") if insp.summary and len(insp.summary) > 500 else (insp.summary or "无总结")
        insp_info.append(f"- ID: {insp.id}, 名称: {insp.name}, 类型: {insp.type}, 内容摘要: {summary_preview}")
    
    prompt = f"""分析以下灵感之间的关系，并生成合适的关系定义。

灵感列表:
{chr(10).join(insp_info)}

请分析这些灵感之间的逻辑关系，返回JSON格式的关系列表。关系类型包括:
- primary: 主从关系（一个灵感是另一个的基础或支撑）
- parallel: 平行关系（两个灵感并列，相互独立但相关）
- contrast: 对比关系（两个灵感形成对比或对立）

返回格式:
{{
  "relations": [
    {{
      "source_id": "源灵感ID",
      "target_id": "目标灵感ID", 
      "relation_type": "primary/parallel/contrast",
      "description": "关系描述"
    }}
  ]
}}

注意:
1. 只返回有意义的关系，不要强行创建关系
2. 描述要简洁明了
3. 关系应该是双向思考的，比如A支撑B，则B依赖A
"""

    response = await client.chat.completions.create(
        model=ai_summarizer.default_config.model_name,
        messages=[
            {"role": "system", "content": "你是一个创意分析专家，擅长分析内容之间的关系。请只返回JSON格式数据，不要有其他文字。"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000
    )
    
    import json
    try:
        content = response.choices[0].message.content
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content.strip())
        return result
    except Exception as e:
        return {"relations": []}


@router.get("/inspirations/search/{query}", response_model=List[Inspiration])
async def search_inspirations(query: str):
    return inspiration_manager.search_inspirations(query)


# ==================== Combinations API ====================

# ==================== Relation Types API ====================

config_manager.init_default_relation_types(DEFAULT_RELATION_TYPES)


class AddRelationTypeRequest(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    style: dict = {"stroke": "#6b7280", "strokeWidth": 2}


class UpdateRelationTypeRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    style: Optional[dict] = None


@router.get("/relation-types", response_model=List[CustomRelationType])
async def list_relation_types():
    types = config_manager.get_relation_types()
    return [CustomRelationType(**t) for t in types]


@router.post("/relation-types", response_model=CustomRelationType)
async def add_relation_type(request: AddRelationTypeRequest):
    rt_dict = {
        "name": request.name,
        "display_name": request.display_name,
        "description": request.description,
        "style": request.style
    }
    saved_rt = config_manager.save_relation_type(rt_dict)
    return CustomRelationType(**saved_rt)


@router.put("/relation-types/{type_id}", response_model=CustomRelationType)
async def update_relation_type(type_id: str, request: UpdateRelationTypeRequest):
    updates = {}
    if request.display_name:
        updates['display_name'] = request.display_name
    if request.description is not None:
        updates['description'] = request.description
    if request.style:
        updates['style'] = request.style
    
    saved_rt = config_manager.update_relation_type(type_id, updates)
    if not saved_rt:
        raise HTTPException(status_code=404, detail="Relation type not found")
    return CustomRelationType(**saved_rt)


@router.delete("/relation-types/{type_id}")
async def delete_relation_type(type_id: str):
    if not config_manager.delete_relation_type(type_id):
        raise HTTPException(status_code=404, detail="Relation type not found")
    return {"success": True}


@router.post("/combinations", response_model=InspirationCombination)
async def create_combination(request: CreateCombinationRequest):
    for insp_id in request.inspiration_ids:
        insp = inspiration_manager.get_inspiration(insp_id)
        if not insp:
            raise HTTPException(status_code=404, detail=f"Inspiration {insp_id} not found")
    
    for sub_id in request.sub_combination_ids:
        sub = config_manager.get_combination(sub_id)
        if not sub:
            raise HTTPException(status_code=404, detail=f"Sub-combination {sub_id} not found")
    
    combination_dict = {
        "name": request.name,
        "description": request.description,
        "inspirations": request.inspiration_ids,
        "sub_combinations": request.sub_combination_ids,
        "relations": [r.model_dump() if hasattr(r, 'model_dump') else r for r in (request.relations or [])]
    }
    
    saved_combination = config_manager.save_combination(combination_dict)
    return InspirationCombination(**saved_combination)


@router.get("/combinations", response_model=List[InspirationCombination])
async def list_combinations():
    combinations = config_manager.get_combinations()
    return [InspirationCombination(**c) for c in combinations]


@router.get("/combinations/{combination_id}", response_model=InspirationCombination)
async def get_combination(combination_id: str):
    combination = config_manager.get_combination(combination_id)
    if not combination:
        raise HTTPException(status_code=404, detail="Combination not found")
    return InspirationCombination(**combination)


@router.put("/combinations/{combination_id}", response_model=InspirationCombination)
async def update_combination(combination_id: str, request: UpdateCombinationRequest):
    existing = config_manager.get_combination(combination_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Combination not found")
    
    updates = {}
    if request.name is not None:
        updates['name'] = request.name
    if request.description is not None:
        updates['description'] = request.description
    if request.inspiration_ids is not None:
        updates['inspirations'] = request.inspiration_ids
    if request.sub_combination_ids is not None:
        updates['sub_combinations'] = request.sub_combination_ids
    if request.relations is not None:
        updates['relations'] = [r.model_dump() if hasattr(r, 'model_dump') else r for r in request.relations]
    
    updated = config_manager.update_combination(combination_id, updates)
    return InspirationCombination(**updated)


@router.delete("/combinations/{combination_id}")
async def delete_combination(combination_id: str):
    if not config_manager.delete_combination(combination_id):
        raise HTTPException(status_code=404, detail="Combination not found")
    return {"success": True}


# ==================== Topologies API ====================

@router.post("/topologies/generate-variants")
async def generate_topology_variants(request: GenerateTopologyVariantsRequest):
    global creative_generator
    
    if not creative_generator:
        raise HTTPException(status_code=400, detail="No AI model configured")
    
    combination_dict = config_manager.get_combination(request.combination_id)
    if not combination_dict:
        raise HTTPException(status_code=404, detail="Combination not found")
    
    combination = InspirationCombination(**combination_dict)
    inspirations = [
        inspiration_manager.get_inspiration(insp_id)
        for insp_id in combination.inspirations
    ]
    inspirations = [i for i in inspirations if i]
    
    node_id_map = {insp.id: insp.name for insp in inspirations}
    
    inspiration_info = "\n".join([
        f"- ID: {insp.id}, 名称: {insp.name}, 类型: {insp.type}, 描述: {insp.summary or '无描述'}"
        for insp in inspirations
    ])
    
    relations_info = "\n".join([
        f"- {node_id_map.get(rel.get('source_id'), rel.get('source_id'))} -> {node_id_map.get(rel.get('target_id'), rel.get('target_id'))}: {rel.get('relation_type')} ({rel.get('description', '无描述')})"
        for rel in request.base_relations
    ]) if request.base_relations else "暂无关系"
    
    prompt = f"""你是一个创意拓扑分析专家。基于以下灵感元素和它们之间的关系，生成两个不同的关系扩展方案。

## 灵感元素:
{inspiration_info}

## 现有关系:
{relations_info}

请分析这些灵感元素之间的潜在关系，为每个方案添加1-2个新的关系连接。新关系应该有意义，能启发新的创意方向。

请以JSON格式返回两个方案，每个方案只包含新增的关系：
[
  {{
    "new_relations": [
      {{
        "source_id": "节点ID",
        "target_id": "节点ID", 
        "relation_type": "primary或parallel或contrast",
        "description": "关系描述"
      }}
    ],
    "description": "这个方案的设计思路"
  }},
  {{
    "new_relations": [
      {{
        "source_id": "节点ID",
        "target_id": "节点ID",
        "relation_type": "primary或parallel或contrast", 
        "description": "关系描述"
      }}
    ],
    "description": "这个方案的设计思路"
  }}
]

注意：
- source_id和target_id必须是上面列出的节点ID
- relation_type必须是 primary、parallel 或 contrast 之一
- 只返回JSON数组，不要有其他文字"""

    try:
        from openai import AsyncOpenAI
        import json
        import re
        import uuid
        
        default_config = config_manager.get_default_model_config()
        if not default_config:
            raise HTTPException(status_code=400, detail="No default AI model configured")
        
        client = AsyncOpenAI(
            api_key=default_config['api_key'],
            base_url=default_config.get('base_url')
        )
        
        response = await client.chat.completions.create(
            model=default_config['model_name'],
            messages=[
                {"role": "system", "content": "你是一个专业的创意拓扑分析专家，擅长分析元素之间的关系并生成有启发性的拓扑变体。只返回JSON，不要有其他文字。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        
        content = response.choices[0].message.content
        print(f"AI Response: {content}")
        
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            variants_data = json.loads(json_match.group())
            
            result = []
            for variant in variants_data:
                new_relations = variant.get('new_relations', [])
                
                import copy
                nodes = copy.deepcopy(request.base_nodes)
                edges = [dict(e) for e in request.base_edges]
                relations = [dict(r) for r in request.base_relations]
                
                for new_rel in new_relations:
                    rel_id = str(uuid.uuid4())
                    rel = {
                        'id': rel_id,
                        'source_id': new_rel['source_id'],
                        'target_id': new_rel['target_id'],
                        'relation_type': new_rel['relation_type'],
                        'description': new_rel.get('description', ''),
                        'created_at': datetime.now().isoformat()
                    }
                    relations.append(rel)
                    
                    edge_config = _get_edge_config(new_rel['relation_type'])
                    edges.append({
                        'id': rel_id,
                        'source': new_rel['source_id'],
                        'target': new_rel['target_id'],
                        'label': f"{_get_relation_label(new_rel['relation_type'])}: {new_rel.get('description', '')}",
                        'type': 'smoothstep',
                        'style': edge_config['style'],
                        'markerEnd': edge_config.get('markerEnd'),
                        'markerStart': edge_config.get('markerStart'),
                        'animated': new_rel['relation_type'] == 'primary',
                        'data': rel,
                        'labelStyle': {'fill': '#374151', 'fontWeight': 500, 'fontSize': '11px'},
                        'labelBgStyle': {'fill': '#ffffff', 'fillOpacity': 0.9},
                        'labelBgPadding': [4, 4],
                        'labelBgBorderRadius': 4
                    })
                
                result.append({
                    'nodes': nodes,
                    'edges': edges,
                    'relations': relations,
                    'description': variant.get('description', '')
                })
            
            return result
        else:
            raise ValueError("No valid JSON array found in response")
            
    except Exception as e:
        print(f"Error generating topology variants: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate topology variants: {str(e)}")


def _get_edge_config(relation_type: str):
    from ..models import MarkerType
    configs = {
        'primary': {
            'style': {'stroke': '#8b5cf6', 'strokeWidth': 2},
            'markerEnd': 'arrow'
        },
        'parallel': {
            'style': {'stroke': '#22c55e', 'strokeWidth': 2}
        },
        'contrast': {
            'style': {'stroke': '#ef4444', 'strokeWidth': 2},
            'markerEnd': 'arrow',
            'markerStart': 'arrow'
        }
    }
    return configs.get(relation_type, configs['parallel'])


def _get_relation_label(relation_type: str):
    labels = {
        'primary': '主从',
        'parallel': '平行',
        'contrast': '对比'
    }
    return labels.get(relation_type, '关系')


# ==================== Creatives API ====================

@router.post("/creatives/generate", response_model=List[Creative])
async def generate_creatives(request: GenerateCreativesRequest):
    global creative_generator
    
    if not creative_generator:
        raise HTTPException(status_code=400, detail="No AI model configured")
    
    combination_dict = config_manager.get_combination(request.combination_id)
    if not combination_dict:
        raise HTTPException(status_code=404, detail="Combination not found")
    
    combination = InspirationCombination(**combination_dict)
    
    if request.relations:
        combination.relations = request.relations
    
    inspirations = [
        inspiration_manager.get_inspiration(insp_id)
        for insp_id in combination.inspirations
    ]
    inspirations = [i for i in inspirations if i]
    
    creatives = await creative_generator.generate_creatives(
        inspirations=inspirations,
        combination=combination,
        count=request.count
    )
    
    saved_creatives = []
    for creative in creatives:
        creative_dict = creative.model_dump() if hasattr(creative, 'model_dump') else creative
        saved = config_manager.save_creative(creative_dict)
        saved_creatives.append(Creative(**saved))
    
    return saved_creatives


@router.post("/creatives/regenerate", response_model=List[Creative])
async def regenerate_creatives(request: RegenerateRequest):
    global creative_generator
    
    if not creative_generator:
        raise HTTPException(status_code=400, detail="No AI model configured")
    
    combination_dict = config_manager.get_combination(request.combination_id)
    if not combination_dict:
        raise HTTPException(status_code=404, detail="Combination not found")
    
    combination = InspirationCombination(**combination_dict)
    inspirations = [
        inspiration_manager.get_inspiration(insp_id)
        for insp_id in combination.inspirations
    ]
    inspirations = [i for i in inspirations if i]
    
    feedback = UserFeedback(
        creative_id="",
        feedback=request.feedback,
        rating=request.rating
    )
    
    creatives = await creative_generator.regenerate_with_feedback(
        inspirations=inspirations,
        combination=combination,
        feedback=feedback,
        count=request.count
    )
    
    saved_creatives = []
    for creative in creatives:
        creative_dict = creative.model_dump() if hasattr(creative, 'model_dump') else creative
        saved = config_manager.save_creative(creative_dict)
        saved_creatives.append(Creative(**saved))
    
    return saved_creatives


@router.get("/creatives", response_model=List[Creative])
async def list_creatives(combination_id: Optional[str] = None):
    creatives = config_manager.get_creatives(combination_id)
    return [Creative(**c) for c in creatives]


@router.get("/creatives/{creative_id}", response_model=Creative)
async def get_creative(creative_id: str):
    creative = config_manager.get_creative(creative_id)
    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")
    return Creative(**creative)


@router.delete("/creatives/{creative_id}")
async def delete_creative(creative_id: str):
    creative = config_manager.get_creative(creative_id)
    if not creative:
        raise HTTPException(status_code=404, detail="Creative not found")
    
    config_manager.delete_creative(creative_id)
    return {"message": "Creative deleted successfully"}


# ==================== Prompts API ====================

@router.post("/prompts/generate", response_model=GeneratedPrompt)
async def generate_prompt(request: GeneratePromptRequest):
    global prompt_generator
    
    if not prompt_generator:
        raise HTTPException(status_code=400, detail="No AI model configured")
    
    creative_dict = config_manager.get_creative(request.creative_id)
    if not creative_dict:
        raise HTTPException(status_code=404, detail="Creative not found")
    
    creative = Creative(**creative_dict)
    inspirations = [
        inspiration_manager.get_inspiration(insp_id)
        for insp_id in request.inspiration_ids
    ]
    inspirations = [i for i in inspirations if i]
    
    prompt = await prompt_generator.generate_prompt(
        creative=creative,
        inspirations=inspirations,
        output_format=request.output_format,
        organize_files=request.organize_files,
        output_folder=request.output_folder
    )
    
    prompt_dict = prompt.model_dump() if hasattr(prompt, 'model_dump') else prompt
    saved_prompt = config_manager.save_prompt(prompt_dict)
    
    return GeneratedPrompt(**saved_prompt)


class GeneratePromptFromCreativeRequest(BaseModel):
    creative_id: str
    regenerate: bool = False


@router.post("/prompts/generate-from-creative")
async def generate_prompt_from_creative(request: GeneratePromptFromCreativeRequest):
    global prompt_generator
    
    if not prompt_generator:
        raise HTTPException(status_code=400, detail="No AI model configured")
    
    creative_dict = config_manager.get_creative(request.creative_id)
    if not creative_dict:
        raise HTTPException(status_code=404, detail="Creative not found")
    
    creative = Creative(**creative_dict)
    
    if creative.prompt and not request.regenerate:
        return {
            "prompt": creative.prompt,
            "aggregated_path": creative.aggregated_path
        }
    
    combination_dict = config_manager.get_combination(creative.combination_id)
    inspirations = []
    if combination_dict:
        for insp_id in combination_dict.get('inspirations', []):
            insp = inspiration_manager.get_inspiration(insp_id)
            if insp:
                inspirations.append(insp)
    
    aggregated_path = creative.aggregated_path
    
    prompt = await prompt_generator.generate_prompt(
        creative=creative,
        inspirations=inspirations,
        output_format="detailed",
        organize_files=False,
        output_folder=None,
        aggregated_path=aggregated_path
    )
    
    creative_dict['prompt'] = prompt.content
    config_manager.save_creative(creative_dict)
    
    return {
        "prompt": prompt.content,
        "aggregated_path": creative.aggregated_path
    }


class AggregateFilesRequest(BaseModel):
    creative_id: str
    output_folder: str


@router.post("/creatives/aggregate-files")
async def aggregate_creative_files(request: AggregateFilesRequest):
    creative_dict = config_manager.get_creative(request.creative_id)
    if not creative_dict:
        raise HTTPException(status_code=404, detail="Creative not found")
    
    creative = Creative(**creative_dict)
    
    combination_dict = config_manager.get_combination(creative.combination_id)
    if not combination_dict:
        raise HTTPException(status_code=404, detail="Combination not found")
    
    inspirations = []
    for insp_id in combination_dict.get('inspirations', []):
        insp = inspiration_manager.get_inspiration(insp_id)
        if insp:
            inspirations.append(insp)
    
    if not inspirations:
        raise HTTPException(status_code=400, detail="No inspirations found for this creative")
    
    import os
    from pathlib import Path
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in creative.title if c.isalnum() or c in (' ', '-', '_')).strip()
    folder_name = f"{safe_name}_{timestamp}"
    
    output_path = Path(request.output_folder) / folder_name
    output_path.mkdir(parents=True, exist_ok=True)
    
    copied_files = []
    
    for insp in inspirations:
        source = Path(insp.path)
        if not source.exists():
            continue
        
        type_folder = output_path / insp.type
        type_folder.mkdir(parents=True, exist_ok=True)
        
        dest = type_folder / source.name
        
        import shutil
        if source.is_file():
            shutil.copy2(source, dest)
            copied_files.append(str(dest))
        else:
            shutil.copytree(source, dest, dirs_exist_ok=True)
            copied_files.append(str(dest))
    
    creative_dict['aggregated_path'] = str(output_path)
    config_manager.save_creative(creative_dict)
    
    return {
        "aggregated_path": str(output_path),
        "files_count": len(copied_files),
        "files": copied_files
    }


@router.get("/prompts/{prompt_id}/export")
async def export_prompt(prompt_id: str, format: str = "markdown"):
    prompt_dict = config_manager.get_prompt(prompt_id)
    if not prompt_dict:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    prompt = GeneratedPrompt(**prompt_dict)
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False, encoding='utf-8') as f:
        if format == "markdown":
            f.write(prompt_generator._to_markdown(prompt))
        else:
            f.write(prompt.content)
        path = f.name
    
    return FileResponse(
        path=path,
        filename=f"prompt_{prompt_id}.{format}",
        media_type="text/plain"
    )


# ==================== Model Config API ====================

@router.post("/config/models", response_model=AIModelConfig)
async def add_model_config(request: ConfigModelRequest):
    if request.is_relation_completer:
        config_manager.clear_relation_completer()
    if request.is_topology_generator:
        config_manager.clear_topology_generator()
    if request.is_inspiration_generator:
        config_manager.clear_inspiration_generator()
    
    config_dict = {
        "name": request.name,
        "provider": request.provider,
        "model_name": request.model_name,
        "api_key": request.api_key,
        "base_url": request.base_url,
        "file_types": request.file_types,
        "is_default": request.is_default,
        "is_relation_completer": request.is_relation_completer,
        "is_topology_generator": request.is_topology_generator,
        "is_inspiration_generator": request.is_inspiration_generator
    }
    
    saved_config = config_manager.save_model_config(config_dict)
    config = AIModelConfig(**saved_config)
    ai_summarizer.register_model(config)
    
    global creative_generator, prompt_generator
    if request.is_default or not creative_generator:
        creative_generator = CreativeGenerator(config)
        prompt_generator = PromptGenerator(config)
    
    return config


@router.get("/config/models", response_model=List[AIModelConfig])
async def list_model_configs():
    configs = config_manager.get_model_configs()
    return [AIModelConfig(**c) for c in configs]


@router.get("/config/models/{model_id}", response_model=AIModelConfig)
async def get_model_config(model_id: str):
    config = config_manager.get_model_config(model_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")
    return AIModelConfig(**config)


@router.put("/config/models/{model_id}", response_model=AIModelConfig)
async def update_model_config(model_id: str, request: ConfigModelRequest):
    updates = {
        "name": request.name,
        "provider": request.provider,
        "model_name": request.model_name,
        "api_key": request.api_key,
        "base_url": request.base_url,
        "file_types": request.file_types,
        "is_default": request.is_default
    }
    
    saved_config = config_manager.update_model_config(model_id, updates)
    if not saved_config:
        raise HTTPException(status_code=404, detail="Model config not found")
    
    config = AIModelConfig(**saved_config)
    ai_summarizer.register_model(config)
    
    global creative_generator, prompt_generator
    if request.is_default:
        creative_generator = CreativeGenerator(config)
        prompt_generator = PromptGenerator(config)
    
    return config


@router.delete("/config/models/{model_id}")
async def delete_model_config(model_id: str):
    if not config_manager.delete_model_config(model_id):
        raise HTTPException(status_code=404, detail="Model config not found")
    return {"status": "deleted"}
