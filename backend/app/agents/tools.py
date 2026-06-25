from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.schemas import Document, DocumentChunk
from backend.app.ingestion.chunker import DocumentChunker
from backend.app.ingestion.graph_extractor import graph_extractor
from graphiti_core.search.search_config import SearchResults
from graphiti_core.search.search_helpers import search_results_to_context_string

# Reuse chunker for query embeddings
chunker = DocumentChunker()

def vector_search_tool(
    db: Session,
    query: str,
    tenant_id: str | None = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search vector database (PostgreSQL + pgvector) for semantic chunks.
    Filters by tenant_id if provided.
    """
    # 1. Generate query embedding
    query_vector = chunker.generate_embeddings([query])[0]

    # 2. Query document chunks and join with documents to get metadata
    query_obj = db.query(DocumentChunk).join(Document)

    # 3. Apply tenant isolation filter
    if tenant_id:
        query_obj = query_obj.filter(Document.metadata_json['tenant_id'].astext == tenant_id)

    # 4. Perform cosine distance search
    vector_results = query_obj.order_by(
        DocumentChunk.embedding.cosine_distance(query_vector)
    ).limit(limit).all()

    # 5. Format results
    formatted_results = []
    for chunk in vector_results:
        formatted_results.append({
            "content": chunk.content,
            "document_id": chunk.document_id,
            "title": chunk.document.title,
            "chunk_index": chunk.chunk_index,
            "source_type": "vector"
        })

    return formatted_results

async def graph_search_tool(
    db: Session,
    query: str,
    tenant_id: str | None = None
) -> Dict[str, Any]:
    """
    Search knowledge graph (Neo4j + Graphiti) for relationships and facts.
    Filters results at the tenant level if tenant_id is provided.
    """
    # 1. Query raw graph search results from Graphiti, passing group_ids for tenant isolation
    group_ids = [tenant_id] if tenant_id else None
    raw_results = await graph_extractor.graphiti.search(query, group_ids=group_ids)

    # Normalize raw_results (handle list vs SearchResults)
    if hasattr(raw_results, "edges"):
        edges_list = raw_results.edges
    else:
        edges_list = raw_results

    # 2. Defense-in-depth: filter by Postgres allowed episode UUIDs if tenant_id is provided
    if tenant_id:
        doc_records = db.query(Document).filter(
            Document.metadata_json['tenant_id'].astext == tenant_id
        ).all()
        
        allowed_episode_uuids = {
            doc.metadata_json.get("graphiti_episode_uuid")
            for doc in doc_records
            if doc.metadata_json and doc.metadata_json.get("graphiti_episode_uuid")
        }

        # Filter edges (facts) to only those originating from allowed episodes
        filtered_edges = [
            edge for edge in edges_list
            if any(ep_uuid in allowed_episode_uuids for ep_uuid in edge.episodes)
        ]
    else:
        filtered_edges = edges_list

    # 3. Format to a context string using a prompt helper JSON serializer
    from graphiti_core.prompts.prompt_helpers import to_prompt_json
    fact_json = [
        {
            'fact': edge.fact,
            'valid_at': str(edge.valid_at) if edge.valid_at else 'date unknown',
            'invalid_at': str(edge.invalid_at) if edge.invalid_at else 'Present',
        }
        for edge in filtered_edges
    ]
    
    context_str = f"""
    FACTS represent relevant context to the current conversation.
    These are the most relevant facts and their valid and invalid dates. Facts are considered valid
    between their valid_at and invalid_at dates. Facts with an invalid_at date of "Present" are considered valid.
    <FACTS>
            {to_prompt_json(fact_json)}
    </FACTS>
    """

    # 4. Resolve source and target entity names to return to UI for network visualizer
    node_names = {}
    node_uuids = set()
    for edge in filtered_edges:
        if hasattr(edge, "source_node_uuid") and edge.source_node_uuid:
            node_uuids.add(edge.source_node_uuid)
        if hasattr(edge, "target_node_uuid") and edge.target_node_uuid:
            node_uuids.add(edge.target_node_uuid)
            
    if node_uuids:
        try:
            nodes_list = await graph_extractor.graphiti.nodes.entity.get_by_uuids(list(node_uuids))
            node_names = {node.uuid: node.name for node in nodes_list}
        except Exception as e:
            print(f"Error resolving entity node names: {e}")

    # 5. Return structured dictionary
    return {
        "context_string": context_str,
        "raw_facts": [
            {
                "fact": edge.fact,
                "name": edge.name,
                "episodes": edge.episodes,
                "source_node_uuid": edge.source_node_uuid,
                "target_node_uuid": edge.target_node_uuid,
                "source_node_name": node_names.get(edge.source_node_uuid, "Unknown"),
                "target_node_name": node_names.get(edge.target_node_uuid, "Unknown")
            }
            for edge in filtered_edges
        ],
        "source_type": "graph"
    }
