export type RelationType = 'primary' | 'parallel' | 'contrast' | 'custom'

export interface CustomRelationType {
  id: string
  name: string
  display_name: string
  description?: string
  style: {
    stroke: string
    strokeWidth: number
    strokeDasharray?: string
    markerEnd?: string
    markerStart?: string
  }
  created_at: string
}

export interface CustomFileType {
  id: string
  name: string
  display_name: string
  extensions: string[]
  icon?: string
  color: string
  description?: string
  text_mode: boolean
  created_at: string
  updated_at: string
}

export interface Inspiration {
  id: string
  name: string
  type: string
  path: string
  summary?: string
  tags: string[]
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface InspirationRelation {
  id: string
  source_id: string
  target_id: string
  relation_type: RelationType
  custom_type_id?: string
  description?: string
  created_at: string
}

export interface InspirationCombination {
  id: string
  name: string
  description?: string
  inspirations: string[]
  sub_combinations: string[]
  relations: InspirationRelation[]
  created_at: string
  updated_at: string
}

export interface Creative {
  id: string
  combination_id: string
  title: string
  description: string
  key_points: string[]
  score?: number
  prompt?: string
  aggregated_path?: string
  created_at: string
}

export interface GeneratedPrompt {
  id: string
  creative_id: string
  content: string
  files: string[]
  created_at: string
}

export interface AIModelConfig {
  id: string
  name: string
  provider: string
  model_name: string
  api_key: string
  base_url?: string
  file_types: string[]
  is_default: boolean
  is_relation_completer?: boolean
  is_topology_generator?: boolean
  is_inspiration_generator?: boolean
}
