export interface Source { title: string; content: string; source_type: string; document_id?: string; score?: number; context_string?: string }
export interface Message { id: string; role: 'user' | 'assistant'; text: string; sources?: Source[]; steps?: string[] }
export interface Conversation { id: string; title: string; tenant_id: string | null; messages?: Message[] }
export interface Document { id: string; title: string; content: string; characters: number; created_at: string; metadata: { status?: string; vector_status?: string; graph_status?: string } | null }
export interface Health { status: string; services: { postgres: boolean; neo4j: boolean; llm: boolean }; provider: string; model: string }

export interface ModelProfile { id: string; provider: string; model: string; label: string; mode: 'local' | 'api'; configured: boolean; available?: boolean | null; status?: string }
export interface ModelCatalog { profiles: ModelProfile[]; local_default_id: string; api_default_id: string | null }
