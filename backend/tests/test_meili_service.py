import pytest
import time
import meilisearch


# All tests in this file require Meilisearch running
pytestmark = pytest.mark.skipif(
    True,  # Set to False when Meilisearch is running
    reason="Set skipif to False when Meilisearch is running"
)


def _wait_for_task(index, task_uid, timeout=10):
    """Wait for a Meilisearch async task to complete."""
    start = time.time()
    while time.time() - start < timeout:
        task = index.get_task(task_uid)
        if task.status == "succeeded":
            return task
        if task.status == "failed":
            raise Exception(f"Task failed: {task.error}")
        time.sleep(0.2)
    raise TimeoutError(f"Task {task_uid} did not complete in {timeout}s")


# Enable tests when Meilisearch is running
del pytestmark


@pytest.fixture(autouse=True)
def clean_index():
    """Delete and recreate index for each test."""
    from services.meili_service import delete_index, setup_index
    delete_index()
    setup_index()
    yield
    delete_index()


class TestIndexCreation:
    """Tests for index creation."""

    def test_index_exists_after_setup(self):
        from config import MEILISEARCH_URL, MEILISEARCH_KEY, MEILISEARCH_INDEX
        client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_KEY)
        indexes = client.get_indexes()
        index_uids = [idx.uid for idx in indexes["results"]]
        assert MEILISEARCH_INDEX in index_uids

    def test_primary_key_is_id(self):
        from services.meili_service import get_index
        index = get_index()
        info = index.fetch_info()
        assert info.primary_key == "id"

    def test_setup_is_idempotent(self):
        """Calling setup_index twice should not error."""
        from services.meili_service import setup_index
        setup_index()  # second call
        from config import MEILISEARCH_URL, MEILISEARCH_KEY, MEILISEARCH_INDEX
        client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_KEY)
        indexes = client.get_indexes()
        index_uids = [idx.uid for idx in indexes["results"]]
        assert MEILISEARCH_INDEX in index_uids


class TestSearchableAttributes:
    """Tests for searchable fields configuration."""

    def test_searchable_attributes_set(self):
        from services.meili_service import get_index
        index = get_index()
        time.sleep(1)  # wait for async update
        settings = index.get_searchable_attributes()
        assert "file_name" in settings

    def test_only_one_searchable_field(self):
        from services.meili_service import get_index
        index = get_index()
        time.sleep(1)
        settings = index.get_searchable_attributes()
        # Should be exactly ["file_name"] (filename-only)
        assert len(settings) == 1


class TestFilterableAttributes:
    """Tests for filterable fields configuration."""

    def test_filterable_attributes_set(self):
        from services.meili_service import get_index
        index = get_index()
        time.sleep(1)
        settings = index.get_filterable_attributes()
        assert "department" in settings
        assert "file_type" in settings
        assert "restricted" in settings

    def test_filterable_fields_count(self):
        from services.meili_service import get_index
        index = get_index()
        time.sleep(1)
        settings = index.get_filterable_attributes()
        assert len(settings) == 5
        for attr in ["department", "file_type", "restricted", "created_at", "modified_at"]:
            assert attr in settings


class TestSortableAttributes:
    """Tests for sortable fields configuration."""

    def test_sortable_attributes_set(self):
        from services.meili_service import get_index
        index = get_index()
        time.sleep(1)
        settings = index.get_sortable_attributes()
        assert "created_at" in settings
        assert "modified_at" in settings
        assert "file_size" in settings


class TestRankingRules:
    """Tests for ranking rules configuration."""

    def test_ranking_rules_set(self):
        from services.meili_service import get_index
        index = get_index()
        time.sleep(1)
        rules = index.get_ranking_rules()
        assert "words" in rules
        assert "typo" in rules
        assert "proximity" in rules
        assert "exactness" in rules
        assert "created_at:desc" in rules

    def test_ranking_order(self):
        from services.meili_service import get_index
        index = get_index()
        time.sleep(1)
        rules = index.get_ranking_rules()
        assert rules[0] == "words"
        assert rules[1] == "typo"


class TestTypoTolerance:
    """Tests for typo tolerance configuration."""

    def test_typo_tolerance_enabled(self):
        from services.meili_service import get_index
        index = get_index()
        time.sleep(1)
        config = index.get_typo_tolerance()
        assert config.enabled is True

    def test_one_typo_threshold(self):
        from services.meili_service import get_index
        index = get_index()
        time.sleep(1)
        config = index.get_typo_tolerance()
        assert config.min_word_size_for_typos.one_typo == 4

    def test_two_typos_threshold(self):
        from services.meili_service import get_index
        index = get_index()
        time.sleep(1)
        config = index.get_typo_tolerance()
        assert config.min_word_size_for_typos.two_typos == 8
