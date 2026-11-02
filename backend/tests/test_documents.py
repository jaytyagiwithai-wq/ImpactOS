import unittest
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.model_registry import load_metadata
from app.modules.documents import service
from app.modules.documents.errors import DocumentNotFound, DocumentStorageUnavailable
from app.modules.documents.models import Document, DocumentVersion
from app.modules.documents.schemas import DocumentCreate
from app.modules.ingestion.loaders import load_doc
from app.modules.organizations.models import Organization
from app.shared.storage.base import EmptyUpload, UploadTooLarge
from app.shared.storage.local import LocalFileStorage


class DocumentServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        with self.engine.begin() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        # This unit suite exercises document registration/upload only. Chunks
        # deliberately use PostgreSQL-only tsvector/pgvector columns, so do
        # not try to compile the retrieval table against SQLite.
        Organization.__table__.create(self.engine)
        Document.__table__.create(self.engine)
        DocumentVersion.__table__.create(self.engine)
        self.session = Session(self.engine, expire_on_commit=False)
        self.org_id = uuid4()
        with self.session.begin():
            self.session.add(Organization(id=self.org_id, name="Test workspace"))

        self.directory = TemporaryDirectory()
        self.storage = LocalFileStorage(Path(self.directory.name) / "uploads")
        self.exporter = InMemorySpanExporter()
        self.provider = TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.tracer_patch = patch.object(
            service, "tracer", self.provider.get_tracer("impactos.documents")
        )
        self.tracer_patch.start()

    def tearDown(self):
        self.tracer_patch.stop()
        self.provider.shutdown()
        self.session.close()
        self.engine.dispose()
        self.directory.cleanup()

    def create_document(self):
        return service.create_document(
            self.session,
            self.org_id,
            DocumentCreate(title="Webhook contract", source_type="openapi"),
        )

    def upload(self, document_id, content=b"customer_id is required", org_id=None):
        return service.upload_document_version(
            session=self.session,
            storage=self.storage,
            org_id=org_id or self.org_id,
            document_id=document_id,
            source=BytesIO(content),
            filename="webhook.md",
            media_type="text/markdown",
        )

    def test_registration_returns_persisted_fields_and_completed_span(self):
        document = self.create_document()
        self.assertEqual(document.source_type, "openapi")
        self.assertEqual(document.status, "registered")
        self.assertEqual(document.org_id, self.org_id)
        self.assertIsNotNone(document.created_at)
        span = self.exporter.get_finished_spans()[-1]
        self.assertEqual(span.attributes["app.outcome"], "success")
        self.assertEqual(span.attributes["app.document.id"], str(document.id))

    def test_upload_preserves_content_and_increments_version(self):
        document = self.create_document()
        content = b"customer_id is required"
        first = self.upload(document.id, content)
        second = self.upload(document.id, b"updated contract")
        self.assertEqual((first.version_number, second.version_number), (1, 2))
        self.assertEqual(first.sha256, sha256(content).hexdigest())
        self.assertEqual(first.byte_size, len(content))
        self.assertNotIn("storage_key", first.model_dump())
        path = self.storage.root / f"{self.org_id}/{document.id}/{first.id}/source"
        self.assertEqual(path.read_bytes(), content)

    def test_cross_tenant_upload_is_rejected_before_storage(self):
        document = self.create_document()
        with patch.object(self.storage, "save_upload") as save:
            with self.assertRaises(DocumentNotFound):
                self.upload(document.id, org_id=uuid4())
        save.assert_not_called()

    def test_empty_and_oversized_uploads_leave_no_file_or_version(self):
        document = self.create_document()
        self.storage = LocalFileStorage(self.storage.root, max_upload_bytes=4)
        for content, error in ((b"", EmptyUpload), (b"12345", UploadTooLarge)):
            with self.subTest(error=error.__name__):
                with self.assertRaises(error):
                    self.upload(document.id, content)
        self.assertEqual(list(self.storage.root.rglob("source*")), [])
        count = self.session.scalar(select(func.count()).select_from(DocumentVersion))
        self.assertEqual(count, 0)

    def test_commit_failure_keeps_file_and_reports_reconciliation(self):
        document = self.create_document()
        commits = 0

        def fail_version_commit(session):
            nonlocal commits
            commits += 1
            if commits == 2:  # Ownership check commits first; version write second.
                raise OperationalError("COMMIT", None, RuntimeError("simulated"))

        event.listen(self.session, "before_commit", fail_version_commit)
        try:
            with self.assertLogs("impactos.documents", level="ERROR") as captured:
                with self.assertRaises(DocumentStorageUnavailable):
                    self.upload(document.id)
        finally:
            event.remove(self.session, "before_commit", fail_version_commit)

        self.assertEqual(len(list(self.storage.root.rglob("source"))), 1)
        record = captured.records[-1]
        self.assertEqual(getattr(record, "app.outcome"), "database_error")
        self.assertTrue(getattr(record, "app.storage.reconciliation_required"))
        span = self.exporter.get_finished_spans()[-1]
        self.assertEqual(span.attributes["app.outcome"], "database_error")
        self.assertTrue(span.attributes["app.storage.reconciliation_required"])
        count = self.session.scalar(select(func.count()).select_from(DocumentVersion))
        self.assertEqual(count, 0)

    def test_storage_span_is_a_child_of_upload_operation(self):
        self.upload(self.create_document().id)
        spans = self.exporter.get_finished_spans()
        upload = next(span for span in spans if span.name == "document_version.upload")
        storage = next(span for span in spans if span.name == "storage.write")
        self.assertEqual(storage.context.trace_id, upload.context.trace_id)
        self.assertEqual(storage.parent.span_id, upload.context.span_id)


class ApplicationContractTests(unittest.TestCase):
    def test_routes_and_document_response_schema(self):
        from app.main import create_app

        schema = create_app().openapi()
        self.assertIn("post", schema["paths"]["/v1/documents"])
        self.assertIn("post", schema["paths"]["/v1/documents/{document_id}/versions"])
        self.assertIn("get", schema["paths"]["/health"])
        self.assertIn("get", schema["paths"]["/health/ready"])
        fields = schema["components"]["schemas"]["DocumentRead"]["properties"]
        self.assertIn("created_at", fields)
        self.assertNotIn("create_at", fields)

    def test_module_models_share_metadata_and_resolve_foreign_keys(self):
        metadata = load_metadata()
        self.assertEqual(
            {table.name for table in metadata.tables.values()},
            {"organizations", "documents", "document_versions", "chunks"},
        )

    def test_loader_preserves_content_and_attaches_version_metadata(self):
        content = "# Webhook\n\n  customer_id is required.\n"
        with TemporaryDirectory() as directory:
            path = Path(directory) / "webhook.md"
            path.write_text(content, encoding="utf-8")
            documents = load_doc(
                path=path,
                source_type="markdown",
                org_id=uuid4(),
                document_id=uuid4(),
                version_id=uuid4(),
            )
        self.assertEqual(documents[0].page_content, content)
        self.assertEqual(documents[0].metadata["source_type"], "markdown")
        self.assertIn("version_id", documents[0].metadata)


if __name__ == "__main__":
    unittest.main()
