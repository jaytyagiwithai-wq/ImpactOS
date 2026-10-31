from dataclasses import dataclass
from openai import OpenAI, APIError
from opentelemetry import trace
from app.core.config import get_settings

tracer = trace.get_tracer("impactos.embedding")

class EmbeddingProviderError(RuntimeError):
    pass

@dataclass()
class EmbeddingBatch:
    vectors: list[list[float]]
    model:str
    prompt_tokens: int


def embed_texts(
        texts: list[str],
        client: OpenAI | None = None
)-> EmbeddingBatch:

    settings = get_settings()

    if not texts:
        return EmbeddingBatch(vectors=[],model=settings.embedding_model,prompt_tokens=0)
    if len(texts) > settings.embedding_batch_size:
        raise ValueError("Embedding batch exceeds batch size")

    if any(not text.strip() for text in texts):
        raise ValueError("Embedding cant have blanks broski")

    client = client or OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=20.0,
        max_retries=2
    )
    attributes = {
        "app.embedding.model": settings.embedding_model,
        "app.embedding.input_count":len(texts),
        "app.embedding.dimensions": settings.embedding_dimensions,
        "app.embedding.outcome": "error"
    }
    with tracer.start_as_current_span("embeddings.create", attributes=attributes) as span:
        try:
            res = client.embeddings.create(
                model=settings.embedding_model,
                input=texts,
                dimensions=settings.embedding_dimensions,
                encoding_format="float"
            )

            
        except APIError as error:
            span.record_exception(error)
            span.set_attribute(
                "embedding.error",type(error).__name__
            )
            raise EmbeddingProviderError("Embedding request failed")

        ordered = sorted(res.data,key=lambda item:item.index)
        vectors = [item.embedding for item in ordered]

        if len(vectors) != len(texts):
            raise EmbeddingProviderError("Embedding response count does not match input count")

        if any(len(vector) != settings.embedding_dimensions for vector in vectors):
            raise  EmbeddingProviderError("Embedding response has an unexpected dims")

        span.set_attribute("app.embedding.prompt_tokens", res.usage.prompt_tokens)
        span.set_attribute("app.embedding.outcome", "success")
        return EmbeddingBatch(
            vectors=vectors,
            model=res.model,
            prompt_tokens=res.usage.prompt_tokens,
        )
