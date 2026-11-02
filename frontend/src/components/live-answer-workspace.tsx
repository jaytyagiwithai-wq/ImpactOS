"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { AlertTriangle, ArrowUpRight, CheckCircle2, Code2, Eye, FileText, LoaderCircle, Send, Sparkles, Upload, X } from "lucide-react";
import { askEvidence, getSourceChunk, inferSourceType, listSources, uploadAndIndexSource, type DocumentVersion, type LiveAnswer, type SourceChunk, type SourceRecord } from "@/lib/live-answer-api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const EXAMPLE_QUESTION = "What must happen before removing customer_id?";
const statusLabel = (status: string) => status === "ready" ? "Indexed" : status === "processing" ? "Indexing" : status === "failed" ? "Failed" : "Uploaded";

export function LiveAnswerWorkspace() {
  const [question, setQuestion] = useState(EXAMPLE_QUESTION);
  const [answer, setAnswer] = useState<LiveAnswer | null>(null);
  const [sources, setSources] = useState<SourceRecord[]>([]);
  const [selectedChunk, setSelectedChunk] = useState<SourceChunk | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingSources, setIsLoadingSources] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadVersion, setUploadVersion] = useState<DocumentVersion | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const requestController = useRef<AbortController | null>(null);
  const fileInput = useRef<HTMLInputElement | null>(null);

  async function refreshSources() {
    setIsLoadingSources(true);
    try { setSources(await listSources()); }
    catch (sourceError) { setError(sourceError instanceof Error ? sourceError.message : "Could not load sources."); }
    finally { setIsLoadingSources(false); }
  }
  useEffect(() => { void refreshSources(); }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = question.trim();
    if (!query || isLoading) return;
    requestController.current?.abort();
    const controller = new AbortController(); requestController.current = controller;
    setIsLoading(true); setError(null); setAnswer(null); setSelectedChunk(null);
    try { setAnswer(await askEvidence(query, controller.signal)); }
    catch (requestError) { if (!(requestError instanceof DOMException && requestError.name === "AbortError")) setError(requestError instanceof Error ? requestError.message : "The request could not be completed."); }
    finally { if (requestController.current === controller) setIsLoading(false); }
  }

  async function uploadSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!file || isUploading) return;
    setIsUploading(true); setError(null);
    try {
      const version = await uploadAndIndexSource({ title: title.trim() || file.name.replace(/\.[^.]+$/, ""), sourceType: inferSourceType(file.name), file, onVersion: setUploadVersion });
      setUploadVersion(version); setFile(null); setTitle("");
      if (fileInput.current) fileInput.current.value = "";
      await refreshSources();
    } catch (uploadError) { setError(uploadError instanceof Error ? uploadError.message : "The source could not be indexed."); }
    finally { setIsUploading(false); }
  }

  async function openChunk(chunkId: string) {
    setError(null);
    try { setSelectedChunk(await getSourceChunk(chunkId)); }
    catch (chunkError) { setError(chunkError instanceof Error ? chunkError.message : "The source chunk is unavailable."); }
  }

  return <div className="live-workspace">
    <section className="live-intro"><span className="live-eyebrow"><Sparkles size={13} /> Live evidence workspace</span><h1>Ask what the current sources support.</h1><p>Upload a source, index it locally, then inspect the exact chunks behind every answer.</p></section>
    <section className="live-source-shelf" aria-labelledby="source-shelf-title">
      <div className="live-shelf-heading"><div><span>Sources</span><h2 id="source-shelf-title">Working set</h2></div><span className="live-source-count">{isLoadingSources ? "Loading" : `${sources.length} files`}</span></div>
      <div className="live-source-list">{sources.slice(0, 5).map(({ document, latest_version }) => <div className="live-source-row" key={document.id}>{document.source_type === "code" ? <Code2 size={15} /> : <FileText size={15} />}<span><strong>{document.title}</strong><small>{latest_version?.original_filename ?? "No version uploaded"}</small></span>{latest_version && <em className={`source-status source-status-${latest_version.status}`}>{statusLabel(latest_version.status)}</em>}</div>)}{!isLoadingSources && sources.length === 0 && <p className="live-empty-source">No sources yet. Add a text, Markdown, OpenAPI, or code file.</p>}</div>
      <form className="live-upload" onSubmit={uploadSource}><input ref={fileInput} id="source-file" type="file" accept=".txt,.md,.mdx,.py,.ts,.tsx,.js,.jsx,.java,.go,.sql,.rb,.cs,.yaml,.yml,.json" onChange={(event) => { const next = event.target.files?.[0] ?? null; setFile(next); if (next && !title) setTitle(next.name.replace(/\.[^.]+$/, "")); }} /><label htmlFor="source-file"><Upload size={15} />{file ? file.name : "Choose a source file"}</label><input aria-label="Source title" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Source title" maxLength={255} /><Button type="submit" size="sm" disabled={!file || isUploading}>{isUploading ? <LoaderCircle className="live-spinner" /> : <ArrowUpRight size={15} />}{isUploading ? "Indexing" : "Add source"}</Button></form>
      {uploadVersion && <p className={`live-upload-status source-status-${uploadVersion.status}`}>{statusLabel(uploadVersion.status)} · version {uploadVersion.version_number} · {uploadVersion.original_filename}</p>}
    </section>
    <form className="live-composer" onSubmit={submit}><label htmlFor="live-question">Question</label><Textarea id="live-question" value={question} onChange={(event) => setQuestion(event.target.value)} rows={3} maxLength={500} placeholder="Ask about a source, dependency, policy, or change…" /><div className="live-composer-footer"><span>Hybrid retrieval · active sources only · cited response</span><Button type="submit" disabled={!question.trim() || isLoading}>{isLoading ? <LoaderCircle className="live-spinner" /> : <Send />}{isLoading ? "Investigating" : "Ask evidence"}</Button></div></form>
    {error && <section className="live-state live-error" role="alert"><AlertTriangle size={18} /><div><strong>Request failed</strong><p>{error}</p></div></section>}
    {answer && <section className="live-answer" aria-live="polite"><div className="live-answer-header"><span className={answer.status === "answered" ? "live-status live-status-ok" : "live-status"}>{answer.status === "answered" ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}{answer.status === "answered" ? "Grounded answer" : "Insufficient evidence"}</span><span className="live-ranking">{answer.ranking_mode === "reranked" ? "Cross-encoder ranked" : "RRF fallback"}</span></div><p className="live-answer-text">{answer.answer}</p>{answer.citations.length > 0 && <div className="live-citations"><h2>Evidence used</h2><div className="live-citation-grid">{answer.citations.map((citation) => <button className="live-citation" key={citation.evidence_id} onClick={() => void openChunk(citation.chunk_id)} type="button"><span className="live-evidence-id">E{citation.evidence_id}</span><FileText size={17} /><div><strong>{citation.document_title}</strong><span>Version {citation.version_number} · chunk {citation.chunk_index}</span></div><Eye size={15} aria-label="Open source chunk" /></button>)}</div></div>}{answer.unknowns.length > 0 && <div className="live-unknowns"><h2>What remains unknown</h2><ul>{answer.unknowns.map((unknown) => <li key={unknown}>{unknown}</li>)}</ul></div>}</section>}
    {selectedChunk && <section className="live-source-view" aria-live="polite"><div className="live-source-view-head"><div><span>Retrieved source</span><h2>{selectedChunk.document_title}</h2><p>{selectedChunk.original_filename} · version {selectedChunk.version_number} · chunk {selectedChunk.chunk_index}</p></div><Button variant="ghost" size="icon" onClick={() => setSelectedChunk(null)} aria-label="Close source"><X size={17} /></Button></div><pre><code>{selectedChunk.content}</code></pre></section>}
  </div>;
}
