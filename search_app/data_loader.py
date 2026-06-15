import csv
import os
import re
from collections import Counter, defaultdict
from functools import lru_cache

try:
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import stopwords
    _nltk_available = True
except Exception:
    WordNetLemmatizer = None
    stopwords = None
    _nltk_available = False

from qalsadi.lemmatizer import Lemmatizer

# Avoid runtime downloads at import time.
# Use NLTK stopwords only if available, otherwise fall back to small static sets.
FALLBACK_ENGLISH_STOPWORDS = {
    'the', 'and', 'is', 'in', 'it', 'of', 'to', 'a', 'for', 'on', 'that', 'this',
    'with', 'as', 'by', 'at', 'from', 'an', 'be', 'are', 'was', 'were', 'or',
    'not', 'have', 'has', 'had', 'but', 'if', 'they', 'you', 'we', 'he', 'she',
    'his', 'her', 'their', 'them', 'which', 'will', 'can', 'would', 'should', 'there'
}
FALLBACK_ARABIC_STOPWORDS = {
    'من', 'في', 'على', 'و', 'لا', 'ما', 'هذا', 'هذه', 'هو', 'هي', 'الى', 'عن',
    'إلى', 'كل', 'انه', 'ان', 'قد', 'ليست', 'كما', 'كان', 'كانت', 'مع', 'يا'
}

if _nltk_available:
    try:
        english_stopwords = set(stopwords.words('english'))
    except Exception:
        english_stopwords = FALLBACK_ENGLISH_STOPWORDS
    try:
        arabic_stopwords = set(stopwords.words('arabic'))
    except Exception:
        arabic_stopwords = FALLBACK_ARABIC_STOPWORDS
else:
    english_stopwords = FALLBACK_ENGLISH_STOPWORDS
    arabic_stopwords = FALLBACK_ARABIC_STOPWORDS

english_lemmatizer = WordNetLemmatizer() if WordNetLemmatizer is not None else None
arabic_lemmatizer = Lemmatizer()

# Cached wrappers to speed up repeated lemmatization calls (notebook-style)
@lru_cache(maxsize=50000)
def _cached_ar_lemmatize(token):
    try:
        # qalsadi can raise or hang on unexpected input; guard and fall back to the token
        return arabic_lemmatizer.lemmatize(token)
    except Exception:
        return token

@lru_cache(maxsize=50000)
def _cached_en_lemmatize(token):
    try:
        return english_lemmatizer.lemmatize(token)
    except Exception:
        return token

ENGLISH_CONTRACTIONS = {
    "i'm": 'i am',
    "he's": 'he is',
    "she's": 'she is',
    "it's": 'it is',
    "that's": 'that is',
    "what's": 'what is',
    "where's": 'where is',
    "how's": 'how is',
    "'ll": ' will',
    "'ve": ' have',
    "'re": ' are',
    "n't": ' not',
}


def preprocess_english(text):
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', ' ', text)
    for contraction, replacement in ENGLISH_CONTRACTIONS.items():
        text = text.replace(contraction, replacement)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    # Faster tokenization: simple split (notebook approach) and cached lemmatizer
    if not text:
        return ''
    tokens = text.split()
    tokens = [_cached_en_lemmatize(token) for token in tokens if token not in english_stopwords]
    return ' '.join(tokens)


# Tunable limits and regex for Arabic token handling
ARABIC_MAX_TOKENS = 1000
ARABIC_WORD_RE = re.compile(r'^[\u0600-\u06FF]{2,30}$')

def preprocess_arabic(text):
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', ' ', text)
    text = re.sub(r'[^\u0600-\u06FF\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return ''
    # Much faster than word_tokenize(): split on whitespace
    tokens = text.split()
    # Cap tokens to avoid pathological long documents
    if len(tokens) > ARABIC_MAX_TOKENS:
        tokens = tokens[:ARABIC_MAX_TOKENS]
    lemmas = []
    for token in tokens:
        if not token or token in arabic_stopwords:
            continue
        # Only run expensive lemmatizer on likely Arabic words of reasonable length
        if ARABIC_WORD_RE.match(token):
            lemma = _cached_ar_lemmatize(token)
        else:
            # keep token as-is (no lemmatization) for numbers/punctuation-heavy tokens
            lemma = token
        lemmas.append(lemma)
    return ' '.join(lemmas)


class DataLoader:
    DATA_FILES = [
        ('arabic', 'arabic.csv'),
        ('english', 'english.csv'),
        ('health', 'health.csv'),
    ]

    # Limit load to the first 5000 Arabic rows to keep preprocessing bounded.
    ARABIC_MAX_ROWS = 5000

    def __init__(self, root=None):
        self.root = root or os.getcwd()
        self.records = []
        self.label_to_ids = defaultdict(list)
        self.completion_terms = []
        self.suggestions = []
        self.record_map = {}
        self.load()

    def load(self):
        token_counter = Counter()
        for source, filename in self.DATA_FILES:
            # Support CSVs directly in the project root or under a `data/` folder
            path = os.path.join(self.root, filename)
            alt_path = os.path.join(self.root, 'data', filename)
            if os.path.exists(path):
                csv_path = path
            elif os.path.exists(alt_path):
                csv_path = alt_path
            else:
                continue

            with open(csv_path, encoding='utf-8', errors='ignore', newline='') as handle:
                reader = csv.reader(handle)
                header = next(reader, None)
                arabic_rows = 0
                for row in reader:
                    if source == 'arabic' and arabic_rows >= self.ARABIC_MAX_ROWS:
                        break
                    if not row:
                        continue
                    text = row[0].strip()
                    label = row[1].strip() if len(row) > 1 else ''
                    if not text:
                        continue

                    normalized_label = label.lower().strip()
                    if source == 'arabic':
                        arabic_rows += 1

                    document_id = len(self.records)
                    record = {
                        'id': document_id,
                        'source': source,
                        'filename': filename,
                        'text': text,
                        'label': label,
                        'normalized_label': normalized_label,
                        'preprocessed': None,
                    }
                    self.records.append(record)
                    self.record_map[document_id] = record

                    if normalized_label:
                        self.label_to_ids[normalized_label].append(document_id)

        # Display labels in their original form (not normalized)
        self.labels = sorted({record['label'] for record in self.records if record['label']})

        # Build a small completion term pool from labels and document words for fuzzy matching
        terms = set()
        for label in self.labels:
            for w in re.findall(r"[\w\u0600-\u06FF']{3,}", label.lower()):
                terms.add(w)
                if len(terms) >= 2000:
                    break
            if len(terms) >= 2000:
                break

        for record in self.records:
            if len(terms) >= 5000:
                break
            for w in re.findall(r"[\w\u0600-\u06FF']{3,}", (record.get('text') or '').lower()):
                terms.add(w)
                if len(terms) >= 5000:
                    break

        self.completion_terms = list(terms)
        self.suggestions = self.labels[:150]

    def get_preprocessed_text(self, record):
        if record.get('preprocessed') is None:
            if record['source'] == 'arabic':
                record['preprocessed'] = preprocess_arabic(record['text'])
            else:
                record['preprocessed'] = preprocess_english(record['text'])
        return record['preprocessed']

    def find_closest_term(self, query, n=1, cutoff=0.7):
        # Use difflib to suggest closest term from labels + completion_terms
        import difflib
        pool = list({t for t in self.completion_terms})
        pool.extend([l for l in self.labels])
        pool = [p for p in pool if p]
        matches = difflib.get_close_matches(query.lower(), pool, n=n, cutoff=cutoff)
        return matches[0] if matches else None

    def is_arabic_query(self, query):
        return bool(re.search(r'[\u0600-\u06FF]', query))

    def preprocess_query(self, query):
        return preprocess_arabic(query) if self.is_arabic_query(query) else preprocess_english(query)

    def get_record(self, document_id):
        return self.record_map.get(document_id)

    def search_by_label(self, query):
        label_key = query.strip().lower()
        ids = self.label_to_ids.get(label_key, [])
        return [self.record_map[doc_id] for doc_id in ids]

    def get_autocomplete(self, prefix, limit=12):
        prefix = prefix.lower().strip()
        if not prefix:
            return self.labels[:limit]

        suggestions = []
        for label in self.labels:
            if label.lower().startswith(prefix):
                suggestions.append(label)
                if len(suggestions) >= limit:
                    return suggestions

        # Also provide sentence completions from document texts when prefix matches
        for record in self.records:
            text = (record.get('text') or '').strip()
            if not text:
                continue
            low = text.lower()
            if low.startswith(prefix) and text not in suggestions:
                # return up to the first sentence or 140 chars
                end = text.find('.')
                snippet = text[:end+1] if end != -1 and end < 140 else text[:140]
                suggestions.append(snippet)
                if len(suggestions) >= limit:
                    return suggestions

        for term in self.completion_terms:
            if term.startswith(prefix) and term not in suggestions:
                suggestions.append(term)
                if len(suggestions) >= limit:
                    break

        return suggestions
