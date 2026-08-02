#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.index import resolve_index_path

STOPWORDS = {
    "a", "al", "algo", "alguna", "algunas", "alguno", "algunos", "ante", "antes", "como", "con",
    "contra", "de", "del", "desde", "donde", "durante", "e", "el", "ella", "ellas", "ello", "ellos",
    "en", "entre", "era", "erais", "eran", "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos",
    "esta", "estaba", "estaban", "estado", "estados", "estamos", "estar", "estas", "este", "esto",
    "estos", "estoy", "fue", "fueron", "ha", "han", "has", "hasta", "hay", "he", "la", "las", "le",
    "les", "lo", "los", "me", "mi", "mis", "mucho", "muchos", "muy", "no", "nos", "nosotras",
    "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "o", "para", "pero", "por", "que",
    "se", "sea", "sean", "ser", "si", "sido", "sin", "sobre", "soy", "su", "sus", "tambien",
    "también", "te", "tiene", "tienen", "tu", "tus", "un", "una", "uno", "unos", "y", "ya",
    "the", "and", "for", "with", "from", "this", "that", "are", "was", "were", "be", "to", "of",
    "in", "on", "at", "or", "an", "is", "it", "as",
}

TOKEN_RE = re.compile(r"[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9_\-]+")
PROJECT_ALIASES = {
    "m360": "Management360",
    "management": "Management360",
    "ventas": "Ventas_Porta",
    "ventasporta": "Ventas_Porta",
    "memento": "mementobloom",
}
PROJECT_PRIORITY = {
    "Management360": 1.15,
    "Ventas_Porta": 1.10,
    "mementobloom": 1.25,
    "docs": 0.95,
}


@dataclass(frozen=True)
class TokenizedEntry:
    entry_id: str
    entry: Dict
    tokens: List[str]
    fields: Dict[str, List[str]]


class MementoOptimizer:
    def __init__(self, index_path: str, backup: bool = True):
        self.index_path = Path(index_path)
        self.backup = backup
        self.memory_root = self.index_path.parent
        self.graph_path = self.index_path.parent / "graph.json"
        self.stats_path = self.index_path.parent / "optimization_stats.json"

    def run(
        self,
        rebuild: bool = True,
        compact: bool = True,
        links: bool = True,
        dry_run: bool = False,
    ) -> Dict:
        if not self.index_path.exists():
            raise FileNotFoundError(f"Índice no encontrado: {self.index_path}")

        original = json.loads(self.index_path.read_text(encoding="utf-8"))
        normalized = self._normalize_entries(original)
        tokenized = [self._tokenize_entry(eid, entry) for eid, entry in normalized.items()]
        vocab = self._build_vocab(tokenized)
        idf = self._build_idf(vocab, len(normalized))

        for item in tokenized:
            item.entry["keywords"] = self._extract_keywords(item, idf)
            item.entry["token_count"] = len(item.tokens)
            item.entry["summary_hash"] = self._hash_text(self._summary_text(item.entry))
            item.entry["path_hash"] = self._hash_text(str(item.entry.get("path", "")))
            item.entry["source_hash"] = self._hash_text(
                self._safe_read_source(item.entry.get("path")) if rebuild else item.entry.get("summary", "")
            )
            item.entry["score"] = self._base_score(item.entry)
            item.entry["last_used_at"] = item.entry.get("last_used_at") or datetime.now().isoformat(timespec="seconds")

        optimized = {eid: entry for eid, entry in sorted(normalized.items())}
        links_out = self._build_links(tokenized, idf) if links else []

        if dry_run:
            return {
                "dry_run": True,
                "total": len(optimized),
                "keywords": sum(1 for e in optimized.values() if e.get("keywords")),
                "links": len(links_out),
                "backup": None,
            }

        if self.backup:
            backup_path = self.index_path.with_suffix(
                self.index_path.suffix + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            shutil.copy2(self.index_path, backup_path)
        else:
            backup_path = None

        self.index_path.write_text(json.dumps(optimized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if compact:
            self.index_path.write_text(json.dumps(optimized, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

        graph = {
            "nodes": list(optimized.keys()),
            "edges": links_out,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "version": "2.0.0",
        }
        self.graph_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        stats = {
            "updated_at": graph["updated_at"],
            "total_entries": len(optimized),
            "by_type": self._count_by_type(optimized),
            "by_project": self._count_by_project(optimized),
            "top_keywords": self._global_top_keywords(tokenized, idf),
            "links": len(links_out),
            "backup": str(backup_path) if backup_path else None,
            "compact": compact,
        }
        self.stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        return {
            "dry_run": False,
            "total": len(optimized),
            "keywords": stats["top_keywords"][:20],
            "links": len(links_out),
            "backup": str(backup_path) if backup_path else None,
        }

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        if not self.index_path.exists():
            return []
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        tokenized_query = self._normalize_text(query)
        if not tokenized_query:
            return []

        vocab = self._build_vocab([self._tokenize_entry(eid, entry) for eid, entry in index.items()])
        idf = self._build_idf(vocab, len(index))
        results = []
        for entry in index.values():
            if not isinstance(entry, dict):
                continue
            score = self._score_entry(entry, tokenized_query, idf)
            if score <= 0:
                continue
            boosted = score * PROJECT_PRIORITY.get(str(entry.get("project", "")), 1.0)
            if self._recent_bonus(entry):
                boosted *= 1.05
            results.append({**entry, "score": round(boosted, 6)})

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    def _normalize_entries(self, original: Dict) -> Dict:
        normalized: Dict[str, Dict] = {}
        seen_hashes: Set[str] = set()
        for raw_id, entry in original.items():
            if not isinstance(entry, dict):
                continue
            eid = str(entry.get("id") or raw_id)
            eid = self._normalize_id(eid)
            if eid in normalized:
                continue
            summary = self._compact_summary(str(entry.get("summary", "")))
            project = self._normalize_project(str(entry.get("project") or "unknown"))
            entry_type = str(entry.get("type") or "UNKNOWN").upper()
            tags = self._normalize_tags(entry.get("tags") or [], project, summary)
            source_hash = self._hash_text(self._safe_read_source(entry.get("path")))
            dedupe_key = f"{entry_type}|{project}|{source_hash or self._hash_text(summary)}"
            if dedupe_key in seen_hashes and entry_type != "CONTEXT":
                continue
            seen_hashes.add(dedupe_key)
            normalized[eid] = {
                "id": eid,
                "type": entry_type,
                "project": project,
                "ts": entry.get("ts", "unknown"),
                "path": entry.get("path", ""),
                "summary": summary,
                "tags": tags,
                "embedding": entry.get("embedding", [0.0] * 384),
                **{k: v for k, v in entry.items() if k not in {"id", "type", "project", "ts", "path", "summary", "tags", "embedding"}},
            }
        return normalized

    def _tokenize_entry(self, entry_id: str, entry: Dict) -> TokenizedEntry:
        text = self._summary_text(entry)
        fields = {
            "title": self._tokens(f"{entry.get('type', '')} {entry.get('project', '')} {entry.get('id', '')}"),
            "tags": self._tokens(" ".join(entry.get("tags", []))),
            "summary": self._tokens(text),
        }
        tokens = fields["title"] + fields["tags"] * 3 + fields["summary"]
        return TokenizedEntry(entry_id=entry_id, entry=entry, tokens=tokens, fields=fields)

    def _build_vocab(self, tokenized: Iterable[TokenizedEntry]) -> Dict[str, Set[str]]:
        vocab: Dict[str, Set[str]] = defaultdict(set)
        for item in tokenized:
            for token in set(item.tokens):
                vocab[token].add(item.entry_id)
        return dict(vocab)

    def _build_idf(self, vocab: Dict[str, Set[str]], total: int) -> Dict[str, float]:
        return {
            token: math.log((total + 1) / (len(docs) + 0.5)) + 1.0
            for token, docs in vocab.items()
        }

    def _extract_keywords(self, item: TokenizedEntry, idf: Dict[str, float]) -> List[str]:
        counts = Counter(item.fields["summary"] + item.fields["tags"])
        scored = []
        for token, count in counts.items():
            if len(token) < 3 or token in STOPWORDS:
                continue
            tf = 1 + math.log(count)
            score = tf * idf.get(token, 1.0)
            scored.append((score, token))
        scored.sort(reverse=True)
        return [token for _, token in scored[:12]]

    def _build_links(self, tokenized: List[TokenizedEntry], idf: Dict[str, float]) -> List[Dict]:
        by_id = {item.entry_id: item for item in tokenized}
        links: List[Dict] = []
        for source in tokenized:
            candidates = []
            source_set = set(source.tokens)
            for target in tokenized:
                if source.entry_id == target.entry_id:
                    continue
                overlap = source_set.intersection(target.tokens)
                if not overlap:
                    continue
                weight = sum(idf.get(t, 1.0) for t in overlap) / math.sqrt(len(source.tokens) + 1)
                candidates.append((weight, target.entry_id, sorted(overlap)[:8]))
            candidates.sort(reverse=True, key=lambda x: x[0])
            for weight, target_id, shared in candidates[:5]:
                if weight >= 2.5:
                    links.append({
                        "source": source.entry_id,
                        "target": target_id,
                        "weight": round(weight, 4),
                        "relationship": "semantic",
                        "shared": shared,
                    })
        return links

    def _score_entry(self, entry: Dict, query_tokens: List[str], idf: Dict[str, float]) -> float:
        entry_text = self._summary_text(entry)
        entry_tokens = self._tokens(entry_text)
        if not entry_tokens:
            return 0.0
        field_tokens = {
            "title": self._tokens(f"{entry.get('type', '')} {entry.get('project', '')} {entry.get('id', '')}"),
            "tags": self._tokens(" ".join(entry.get("tags", []))),
            "keywords": self._tokens(" ".join(entry.get("keywords", []))),
            "summary": entry_tokens,
        }
        score = 0.0
        field_weight = {"title": 3.0, "tags": 2.5, "keywords": 2.0, "summary": 1.0}
        for field, tokens in field_tokens.items():
            counts = Counter(tokens)
            field_len = len(tokens) or 1
            for q in query_tokens:
                tf = counts.get(q, 0)
                if not tf:
                    continue
                tf_score = (1 + math.log(tf)) / (1 + math.log(field_len))
                score += field_weight[field] * tf_score * idf.get(q, 1.0)
        query_overlap = len(set(query_tokens).intersection(entry_tokens))
        if query_overlap:
            score *= 1 + (query_overlap / len(query_tokens))
        return score

    def _base_score(self, entry: Dict) -> float:
        score = len(entry.get("keywords", [])) * 0.2 + len(entry.get("tags", [])) * 0.1
        if entry.get("type") == "HANDOFF":
            score += 1.0
        if entry.get("type") == "CONTEXT":
            score += 0.7
        return round(score, 4)

    def _recent_bonus(self, entry: Dict) -> bool:
        ts = str(entry.get("ts", ""))
        return bool(re.search(r"2026-06-1[123]", ts))

    def _summary_text(self, entry: Dict) -> str:
        return " ".join(
            str(part)
            for part in [
                entry.get("id", ""),
                entry.get("type", ""),
                entry.get("project", ""),
                " ".join(entry.get("tags", [])),
                " ".join(entry.get("keywords", [])),
                entry.get("summary", ""),
            ]
            if part
        )

    def _compact_summary(self, summary: str) -> str:
        text = re.sub(r"\s+", " ", summary).strip()
        return text[:900]

    def _normalize_id(self, value: str) -> str:
        value = value.strip().replace(" ", "_")
        return re.sub(r"[^a-zA-Z0-9_\-\.\:]+", "", value)

    def _normalize_project(self, value: str) -> str:
        key = re.sub(r"[^a-zA-Z0-9]+", "", value).lower()
        return PROJECT_ALIASES.get(key, value)

    def _normalize_tags(self, tags: object, project: str, summary: str) -> List[str]:
        if isinstance(tags, str):
            tags = [tags]
        elif not isinstance(tags, list):
            tags = []
        normalized = {self._normalize_tag(t) for t in tags if self._normalize_tag(t)}
        normalized.add(project)
        for token in self._tokens(summary):
            if token in {"ubigeo", "venta", "ventas", "trazabilidad", "modelo", "refactor", "vault", "credenciales"}:
                normalized.add(token)
            if len(normalized) >= 16:
                break
        return sorted(normalized)

    def _normalize_tag(self, tag: object) -> str:
        text = str(tag or "").strip().lower()
        text = re.sub(r"[^a-z0-9áéíóúñü_\-\s]+", " ", text)
        text = re.sub(r"\s+", "_", text)
        return text[:32]

    def _safe_read_source(self, path: object) -> str:
        try:
            p = Path(str(path))
            if p.exists() and p.is_file():
                return p.read_text(encoding="utf-8", errors="ignore")[:2000]
        except Exception:
            return ""
        return ""

    def _tokens(self, text: str) -> List[str]:
        return [t.lower() for t in TOKEN_RE.findall(text) if len(t) > 1]

    def _normalize_text(self, text: str) -> List[str]:
        return [t for t in self._tokens(text) if t not in STOPWORDS]

    def _hash_text(self, text: str) -> str:
        h = 5381
        for char in text:
            h = ((h << 5) + h + ord(char)) & 0xFFFFFFFF
        return f"{h:08x}"

    def _count_by_type(self, entries: Dict) -> Dict[str, int]:
        counts = Counter(entry.get("type", "UNKNOWN") for entry in entries.values())
        return dict(sorted(counts.items()))

    def _count_by_project(self, entries: Dict) -> Dict[str, int]:
        counts = Counter(entry.get("project", "unknown") for entry in entries.values())
        return dict(sorted(counts.items()))

    def _global_top_keywords(self, tokenized: List[TokenizedEntry], idf: Dict[str, float]) -> List[Dict]:
        counts = Counter()
        for item in tokenized:
            counts.update(item.fields["summary"])
            counts.update(item.fields["tags"])
        rows = []
        for token, count in counts.most_common(200):
            if len(token) < 3 or token in STOPWORDS:
                continue
            rows.append({"keyword": token, "count": count, "idf": round(idf.get(token, 1.0), 4)})
        rows.sort(key=lambda r: (r["idf"] * math.log(r["count"] + 1), r["count"]), reverse=True)
        return rows[:80]


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimiza el índice de memoria MementoBloom")
    parser.add_argument("--index", default=None, help="Ruta del índice de memoria")
    parser.add_argument("--search")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--rebuild", action="store_true", help="Reconstruye hashes y metadata desde fuentes")
    parser.add_argument("--compact", action="store_true", help="Compacta el JSON del índice")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--no-links", action="store_true")
    parser.add_argument("--no-compact", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-rebuild", action="store_true")
    args = parser.parse_args()

    index_path = args.index if args.index else None
    optimizer = MementoOptimizer(resolve_index_path(index_path), backup=not args.no_backup)
    if args.search:
        results = optimizer.search(args.search, args.limit)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    compact_requested = args.compact
    rebuild_requested = args.rebuild
    result = optimizer.run(
        rebuild=(not args.no_rebuild) and (rebuild_requested or not args.dry_run),
        compact=(not args.no_compact) and (compact_requested or not args.dry_run),
        links=not args.no_links,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
