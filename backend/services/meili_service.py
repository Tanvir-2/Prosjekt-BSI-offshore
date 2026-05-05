import meilisearch
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from meilisearch import Client as MeiliClient, Index as MeiliIndex

from config import MEILISEARCH_URL, MEILISEARCH_KEY, MEILISEARCH_INDEX


def get_client():
    """Return a Meilisearch client."""
    return meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_KEY)


def get_index():
    """Return the bsi_documents index."""
    return get_client().index(MEILISEARCH_INDEX)


def setup_index():
    """Create and configure the bsi_documents index.

    Call once on backend startup. Safe to call multiple times.
    """
    client = get_client()

    # Create index if it doesn't exist
    try:
        client.create_index(MEILISEARCH_INDEX, {"primaryKey": "id"})
    except meilisearch.errors.MeilisearchApiError:
        pass  # Index already exists

    index = client.index(MEILISEARCH_INDEX)

    
    index.update_searchable_attributes(["file_name"])

    
    index.update_filterable_attributes([
        "department", "file_type", "restricted",
        "created_at", "modified_at",
    ])

    
    index.update_sortable_attributes(["created_at", "modified_at", "file_size"])

    
    index.update_ranking_rules([
        "words",
        "typo",
        "proximity",
        "exactness",
        "sort",
        "created_at:desc",
    ])

   
    index.update_typo_tolerance({
        "enabled": True,
        "minWordSizeForTypos": {
            "oneTypo": 4,
            "twoTypos": 8,
        }
    })

    return index


def delete_index():
    """Delete the entire index. Used for clean test setups."""
    client = get_client()
    try:
        client.delete_index(MEILISEARCH_INDEX)
    except meilisearch.errors.MeilisearchApiError:
        pass  # Index doesn't exist


def add_document(doc):
    """Add or update a single document in the index."""
    index = get_index()
    task = index.add_documents([doc])
    index.wait_for_task(task.task_uid)
    return task


def add_documents(docs):
    """Add or update multiple documents in the index."""
    if not docs:
        return None
    index = get_index()
    task = index.add_documents(docs)
    index.wait_for_task(task.task_uid)
    return task


def remove_document(doc_id):
    """Remove a single document by its ID."""
    index = get_index()
    task = index.delete_document(doc_id)
    index.wait_for_task(task.task_uid)
    return task


def get_document(doc_id):
    """Get a single document by its ID. Returns a dict."""
    index = get_index()
    doc = index.get_document(doc_id)
    return dict(doc)


def get_document_count():
    """Return the total number of documents in the index."""
    index = get_index()
    stats = index.get_stats()
    return stats.number_of_documents


def bulk_index(data_root=None, batch_size=500):
    """Scan directory, build documents, and push to Meilisearch in batches.

    Returns (total_indexed, errors_count).
    """
    import logging
    from services.ingestion import scan_directory
    logger = logging.getLogger(__name__)

    documents = scan_directory(data_root)
    total = len(documents)
    logger.info(f"Bulk indexing {total} documents in batches of {batch_size}")

    for i in range(0, total, batch_size):
        batch = documents[i:i + batch_size]
        add_documents(batch)
        logger.info(f"Indexed batch {i // batch_size + 1}: {len(batch)} documents")

    logger.info(f"Bulk indexing complete: {total} documents")
    return total


def search_documents(query, filters=None, limit=20, offset=0, sort=None):
    """Search documents with optional filters, pagination, and sorting.

    Args:
        query: Search string (empty string returns all documents)
        filters: List of Meilisearch filter expressions, e.g. ["department = HR"]
        limit: Max results to return (default 20)
        offset: Pagination offset (default 0)
        sort: List of sort expressions, e.g. ["created_at:desc"]

    Returns:
        Meilisearch search results dict with hits, estimatedTotalHits, query, etc.
    """
    index = get_index()
    params = {
        "attributesToHighlight": ["file_name"],
        "limit": limit,
        "offset": offset,
    }
    if filters:
        params["filter"] = filters
    if sort:
        params["sort"] = sort
    return index.search(query, params)


def _get_highlight(hit):
    """Extract the filename highlight from a hit."""
    formatted = hit.get("_formatted", {})
    file_name = formatted.get("file_name", "")
    if file_name and "<em>" in file_name:
        return file_name
    return hit.get("file_name", "")


def format_search_response(raw_results, query=""):
    """Transform raw Meilisearch results into a clean frontend-ready response.

    Returns:
        {
            "query": str,
            "total_hits": int,
            "limit": int,
            "offset": int,
            "results": [
                {
                    "id": str,
                    "file_name": str,
                    "department": str,
                    "file_type": str,
                    "file_size": int,
                    "created_at": str,
                    "modified_at": str,
                    "highlight": str,
                },
                ...
            ]
        }
    """
    hits = raw_results.get("hits", [])
    results = []
    for hit in hits:
        results.append({
            "id": hit.get("id", ""),
            "file_name": hit.get("file_name", ""),
            "department": hit.get("department", ""),
            "file_type": hit.get("file_type", ""),
            "file_size": hit.get("file_size", 0),
            "created_at": hit.get("created_at", ""),
            "modified_at": hit.get("modified_at", ""),
            "highlight": _get_highlight(hit),
        })
    return {
        "query": query,
        "total_hits": raw_results.get("estimatedTotalHits", 0),
        "limit": raw_results.get("limit", 20),
        "offset": raw_results.get("offset", 0),
        "results": results,
    }


def get_department_filter(user_role):
    """Return Meilisearch filter based on user role.

    Driftsmøter is visible to all logged-in users.
    Admin sees everything (returns None = no filter).
    """
    from config import ROLE_DEPARTMENT_ACCESS
    access = ROLE_DEPARTMENT_ACCESS.get(user_role)
    if access is None:
        return None  
    
    departments = ", ".join(access)
    return [f"department IN [{departments}]"]
