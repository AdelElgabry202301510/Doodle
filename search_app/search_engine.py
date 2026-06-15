import os
import numpy as np
from sentence_transformers import SentenceTransformer
import json
import math
import requests
import time
import itertools
from .data_loader import DataLoader

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))

class SearchEngine:
    def __init__(self, loader: DataLoader):
        self.loader = loader
        self.arabic_model = None
        self.english_model = None
        self.remote_enabled = False
        self.arabic_docs = []
        self.non_arabic_docs = []
        self.arabic_embeddings = None
        self.non_arabic_embeddings = None
        self._models_loaded = False
        self._embeddings_built = False
        self._configure_model_paths()

    def _configure_model_paths(self):
        self.local_english_path = os.path.join(MODEL_DIR, 'english_model')
        self.local_arabic_path = os.path.join(MODEL_DIR, 'arabic_model')

        use_remote = os.getenv('USE_HF_INFERENCE', '').lower() in ('1', 'true', 'yes')
        hf_token = os.getenv('HF_API_TOKEN', '')
        self.remote_enabled = use_remote and bool(hf_token)
        self.semantic_enabled = self.remote_enabled

    def _ensure_embeddings(self):
        self._load_models()
        if not self._embeddings_built:
            self._build_embeddings()
            self._embeddings_built = True

    def _load_models(self):
        if self._models_loaded:
            return
        self._models_loaded = True

        if os.path.isdir(self.local_english_path):
            try:
                self.english_model = SentenceTransformer(self.local_english_path, device='cpu')
            except Exception:
                self.english_model = None

        if os.path.isdir(self.local_arabic_path):
            try:
                self.arabic_model = SentenceTransformer(self.local_arabic_path, device='cpu')
            except Exception:
                self.arabic_model = None

        # If local models are missing and remote is not enabled, disable semantics.
        if not self.remote_enabled and self.arabic_model is None and self.english_model is None:
            self.semantic_enabled = False

    def _build_embeddings(self):
        self.arabic_docs = [record for record in self.loader.records if record['source'] == 'arabic']
        self.non_arabic_docs = [record for record in self.loader.records if record['source'] != 'arabic']
        if self.semantic_enabled:
            self._load_models()
            if self.arabic_docs and self.arabic_model is not None:
                self.arabic_embeddings = self.arabic_model.encode(
                    [record.get('preprocessed', record['text']) for record in self.arabic_docs],
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )

            if self.non_arabic_docs and self.english_model is not None:
                self.non_arabic_embeddings = self.english_model.encode(
                    [record.get('preprocessed', record['text']) for record in self.non_arabic_docs],
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )

            if self.remote_enabled and not (self.arabic_embeddings is not None and self.non_arabic_embeddings is not None):
                if self.arabic_docs:
                    texts = [record.get('preprocessed', record['text']) for record in self.arabic_docs]
                    self.arabic_embeddings = self._hf_embed_batch('Adel-Elgabry/arabic-semantic-search', texts)
                if self.non_arabic_docs:
                    texts = [record.get('preprocessed', record['text']) for record in self.non_arabic_docs]
                    self.non_arabic_embeddings = self._hf_embed_batch('Adel-Elgabry/english-semantic-search', texts)
        else:
            # Ensure embeddings are None when semantic mode is disabled
            self.arabic_embeddings = None
            self.non_arabic_embeddings = None

    def _score_embeddings(self, query_embedding, embeddings):
        if embeddings is None or query_embedding is None:
            return []
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        return np.dot(embeddings, query_norm)

    def _hf_embed_batch(self, model_name, texts, batch_size=32, retry=3, pause=1.0):
        """Call HF Inference embeddings endpoint in batches and return normalized numpy array."""
        hf_token = os.getenv('HF_API_TOKEN', '')
        if not hf_token:
            raise RuntimeError('HF_API_TOKEN not set for remote inference')

        url = 'https://api-inference.huggingface.co/embeddings'
        headers = {'Authorization': f'Bearer {hf_token}', 'Content-Type': 'application/json'}
        all_emb = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            payload = {'model': model_name, 'input': batch}
            for attempt in range(retry):
                try:
                    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
                    if resp.status_code == 200:
                        data = resp.json()
                        # Expect data to be list of embeddings or dict with 'embeddings'
                        if isinstance(data, dict) and 'error' in data:
                            raise RuntimeError(f"HF error: {data['error']}")
                        # data may be list of dicts or list of lists
                        if isinstance(data, dict) and 'embeddings' in data:
                            emb = data['embeddings']
                        else:
                            emb = [d['embedding'] if isinstance(d, dict) and 'embedding' in d else d for d in data]
                        all_emb.extend(emb)
                        break
                    else:
                        time.sleep(pause)
                except Exception:
                    time.sleep(pause)
            else:
                raise RuntimeError('Failed to fetch embeddings from HF after retries')

        arr = np.array(all_emb, dtype=float)
        # normalize
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        arr = arr / norms
        return arr

    def _snippet(self, text, query):
        clean_text = text.replace('\n', ' ')
        query_lower = query.lower().strip()
        index = clean_text.lower().find(query_lower)
        if index < 0:
            return clean_text[:220] + ('...' if len(clean_text) > 220 else '')
        start = max(0, index - 80)
        end = min(len(clean_text), index + 220)
        snippet = clean_text[start:end]
        if start > 0:
            snippet = '...' + snippet
        if end < len(clean_text):
            snippet = snippet + '...'
        return snippet

    def _record_view(self, record, score, query, exact=False):
        # Title: use first sentence of the document if present, else label
        text = (record.get('text') or '').strip()
        first_sent = ''
        if text:
            end = text.find('.')
            if end != -1:
                first_sent = text[:end+1]
            else:
                first_sent = text.split('\n', 1)[0][:120]
        title = first_sent if first_sent else (record.get('label') or f'{record["source"].title()} Document')
        return {
            'id': record['id'],
            'source': record['source'],
            'title': title,
            'snippet': self._snippet(record['text'], query),
            'score': float(score),
            'exact': exact,
        }

    def _keyword_matches(self, query):
        query_lower = query.lower().strip()
        hits = []
        for record in self.loader.records:
            if query_lower in record['text'].lower() or query_lower in record['label'].lower():
                hits.append(self._record_view(record, 0.25, query))
        return hits

    def _rank_results(self, docs, scores, query):
        ranked = []
        for record, score in sorted(zip(docs, scores), key=lambda pair: -pair[1])[:40]:
            ranked.append(self._record_view(record, float(score), query))
        return ranked

    def search(self, query, limit=20):
        query = query.strip()
        if not query:
            return []

        label_results = self.loader.search_by_label(query)
        if label_results:
            return [self._record_view(record, 1.0, query, exact=True) for record in label_results]

        # If semantic search is enabled (local models present), use it.
        results = []
        if self.semantic_enabled:
            # Ensure embeddings are available (build lazily)
            try:
                self._ensure_embeddings()
            except Exception:
                # If embedding build fails, fall back to keyword-only search
                self.arabic_embeddings = None
                self.non_arabic_embeddings = None
                self._embeddings_built = False
            query_text = self.loader.preprocess_query(query)
            if self.loader.is_arabic_query(query) and self.arabic_embeddings is not None and self.arabic_model is not None:
                q_emb = self.arabic_model.encode(
                    [query_text],
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )[0]
                scores = self._score_embeddings(q_emb, self.arabic_embeddings)
                results.extend(self._rank_results(self.arabic_docs, scores, query))
            elif self.non_arabic_embeddings is not None and self.english_model is not None:
                q_emb = self.english_model.encode(
                    [query_text],
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                )[0]
                scores = self._score_embeddings(q_emb, self.non_arabic_embeddings)
                results.extend(self._rank_results(self.non_arabic_docs, scores, query))
        else:
            # Semantic models are disabled: we'll rely on keyword matches only.
            results = []

        keyword_hits = self._keyword_matches(query)
        merged = {item['id']: item for item in results}
        for item in keyword_hits:
            if item['id'] not in merged:
                merged[item['id']] = item

        sorted_results = sorted(merged.values(), key=lambda item: (-item['score'], not item['exact']))
        # If no results, attempt fuzzy correction and retry once
        if not sorted_results:
            try:
                correction = self.loader.find_closest_term(query)
                if correction and correction.lower() != query.lower():
                    return self.search(correction, limit=limit)
            except Exception:
                pass
        return sorted_results[:limit]

    def autocomplete(self, prefix):
        return self.loader.get_autocomplete(prefix)
