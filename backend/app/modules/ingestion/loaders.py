from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from uuid import UUID
from pathlib import Path

MAX_FILE_BYTES = 10*1024*1024

def load_doc(
        path: Path,
        source_type: str,
        org_id: UUID,
        document_id: UUID,
        version_id: UUID
)-> list[Document]:
    if source_type not in ["text","markdown"]:
        raise ValueError("Only text and Markdowns are supported")

    size = path.stat().st_size

    if size==0:
        raise ValueError("File is empty")

    if size > MAX_FILE_BYTES:
        raise ValueError("File exceeds 10 Mib") 

    documents = TextLoader(
        str(path),
        encoding="utf-8"
    ).load()


    for document in documents:
        content = document.page_content

        if not content.strip():
            raise ValueError("Document contains no readable text")

        if "\x00" in content:
            raise ValueError("Document contains unsupported null characters")

        document.metadata = {
            "org_id": str(org_id),
            "document_id": str(document_id),
            "version_id": str(version_id),
            "source_type": source_type,
        }

    return documents