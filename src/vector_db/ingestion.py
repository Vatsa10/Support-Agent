from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re


class AdvancedChunkingStrategy:
    """Intelligent chunking with semantic awareness"""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n## ",  # Markdown headers
                "\n\n### ",
                "\n\n",  # Paragraph breaks
                "\n",  # Line breaks
                ". ",  # Sentences
                " ",  # Words
                "",
            ],
        )

    def extract_metadata(self, text: str, source: str) -> dict:
        """Extract semantic metadata from chunk"""

        # Find headers
        header_match = re.search(r"^#+\s+(.+)$", text, re.MULTILINE)
        section = header_match.group(1) if header_match else "General"

        # Estimate category
        category = self._classify_category(text)

        # Extract key phrases
        key_phrases = self._extract_keyphrases(text)

        return {
            "source": source,
            "section": section,
            "category": category,
            "key_phrases": key_phrases,
            "length": len(text),
            "searchable": True,
        }

    def _classify_category(self, text: str) -> str:
        """Classify chunk category"""
        text_lower = text.lower()

        if any(
            word in text_lower for word in ["billing", "payment", "invoice", "charge"]
        ):
            return "billing"
        elif any(word in text_lower for word in ["technical", "bug", "error", "crash"]):
            return "technical"
        elif any(word in text_lower for word in ["shipping", "delivery", "track"]):
            return "shipping"
        elif any(word in text_lower for word in ["return", "refund", "exchange"]):
            return "returns"
        else:
            return "general"

    def _extract_keyphrases(self, text: str, top_n: int = 5) -> List[str]:
        """Extract important phrases from text"""
        # Simple keyphrase extraction (can be enhanced with NLP)
        sentences = text.split(". ")
        phrases = []

        for sentence in sentences[:top_n]:
            # Take first 10 words as keyphrase
            phrase = " ".join(sentence.split()[:10])
            if phrase:
                phrases.append(phrase)

        return phrases[:top_n]

    def chunk_with_metadata(self, text: str, source: str) -> List[dict]:
        """Split text into chunks with metadata"""

        chunks = self.splitter.split_text(text)

        chunk_objects = []
        for i, chunk in enumerate(chunks):
            metadata = self.extract_metadata(chunk, source)
            metadata["chunk_id"] = f"{source}_{i}"

            chunk_objects.append(
                {"id": metadata["chunk_id"], "text": chunk, "metadata": metadata}
            )

        return chunk_objects


def load_knowledge_base(kb_path: str, tenant_id: str = None) -> List[dict]:
    """Load and chunk knowledge base documents.

    If tenant_id provided, reads from <kb_path>/<tenant_id>/.
    Otherwise reads from kb_path directly (legacy / single-tenant fallback).
    """

    import os

    chunker = AdvancedChunkingStrategy(chunk_size=800, chunk_overlap=200)
    all_chunks = []

    supported_extensions = [".txt", ".md", ".csv", ".json", ".html", ".htm"]

    target = os.path.join(kb_path, tenant_id) if tenant_id else kb_path

    if not os.path.exists(target):
        print(f"Knowledge base path does not exist: {target}")
        return []

    file_count = 0

    for filename in os.listdir(target):
        ext = os.path.splitext(filename)[1].lower()

        if ext not in supported_extensions:
            continue

        file_count += 1
        filepath = os.path.join(target, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                print(f"⚠️ Skipping empty file: {filename}")
                continue

            chunks = chunker.chunk_with_metadata(content, filename)
            all_chunks.extend(chunks)

            print(f"✅ Loaded {len(chunks)} chunks from {filename}")

        except Exception as e:
            print(f"⚠️ Error loading {filename}: {e}")

    print(f"📚 Total: {file_count} files, {len(all_chunks)} chunks loaded")
    return all_chunks
