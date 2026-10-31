import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# another model-dependent failure point + cost + latency - semantic chunking



def chunk_docs(
        documents: list[Document],
        max_tokens: int = 500,
        overalp_tokens: int = 75
):
    if max_tokens <= 0:
        raise ValueError("The the msx_tokens must be positive")

    if not 0 <= overalp_tokens < max_tokens:
        raise ValueError("Overlap must between 0 and max_tokens")


    encoding = tiktoken.get_encoding(
        "cl100k_base"
    )  

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size = max_tokens,
        chunk_overlap=overalp_tokens,
        strip_whitespace=False,
        add_start_index=False,
        disallowed_special=(),

    )      

    chunks = [
        chunk
        for chunk in splitter.split_documents(documents)
        if chunk.page_content.strip()
    ]

    for i, chunk in enumerate(chunks):
        token_count = len(
            encoding.encode_ordinary(chunk.page_content)

        )

        if token_count > max_tokens:
            raise RuntimeError("Chunk exceeds the token budget")

        chunk.metadata.update({
            "chunk_index": i,
            "token_count": token_count,
            "chunker_version": "recursive-v1",
            "max_tokens": max_tokens,
            "overlap_tokens": overalp_tokens,
            "tokenizer": "cl100k_base",
        })

    return chunks

