from types import SimpleNamespace

import pytest

from app.modules.ingestion import embeddings


class FakeEmbeddings:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.embeddings = FakeEmbeddings(response)


@pytest.fixture
def settings(monkeypatch):
    fake_settings = SimpleNamespace(
        embedding_model="text-embedding-3-small",
        embedding_dimensions=3,
        embedding_batch_size=2,
    )
    monkeypatch.setattr(embeddings, "get_settings", lambda: fake_settings)


def test_embed_texts_sorts_response_and_returns_usage(settings):
    response = SimpleNamespace(
        data=[
            SimpleNamespace(index=1, embedding=[0.4, 0.5, 0.6]),
            SimpleNamespace(index=0, embedding=[0.1, 0.2, 0.3]),
        ],
        model="text-embedding-3-small",
        usage=SimpleNamespace(prompt_tokens=7),
    )
    client = FakeClient(response)

    result = embeddings.embed_texts(["first", "second"], client=client)

    assert result.vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    assert result.model == "text-embedding-3-small"
    assert result.prompt_tokens == 7
    assert client.embeddings.calls[0]["input"] == ["first", "second"]


def test_embed_texts_rejects_wrong_vector_dimension(settings):
    response = SimpleNamespace(
        data=[SimpleNamespace(index=0, embedding=[0.1, 0.2])],
        model="text-embedding-3-small",
        usage=SimpleNamespace(prompt_tokens=2),
    )

    with pytest.raises(embeddings.EmbeddingProviderError):
        embeddings.embed_texts(["hello"], client=FakeClient(response))