import pytest
import meilisearch


class TestMeilisearchConnection:
    """Tests for Meilisearch connectivity."""

    def test_meilisearch_is_running(self):
        from config import MEILISEARCH_URL, MEILISEARCH_KEY
        client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_KEY)
        health = client.health()
        assert health["status"] == "available"

    def test_meilisearch_version(self):
        from config import MEILISEARCH_URL, MEILISEARCH_KEY
        client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_KEY)
        version = client.get_version()
        assert "pkgVersion" in version

    def test_can_list_indexes(self):
        from config import MEILISEARCH_URL, MEILISEARCH_KEY
        client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_KEY)
        indexes = client.get_indexes()
        assert isinstance(indexes, dict) or isinstance(indexes, list)

    def test_master_key_is_set(self):
        """Without the correct key, requests should fail."""
        from config import MEILISEARCH_URL
        client = meilisearch.Client(MEILISEARCH_URL, "wrong-key")
        with pytest.raises(Exception):
            client.get_indexes()
