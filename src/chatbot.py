"""
src/chatbot.py
---------------
A simple NLP-based (TF-IDF + Cosine Similarity) customer-service chatbot.

NLP Techniques used (project explanation):
1. Text Preprocessing -> lowercasing, punctuation removal, tokenization,
   stopword removal (keeps the pipeline dependency-free — no external
   NLTK data downloads needed, so it works offline / on any server).
2. Vectorization -> TF-IDF (Term Frequency - Inverse Document Frequency)
   converts text patterns into numeric vectors.
3. Similarity Matching -> Cosine Similarity finds the closest known
   pattern to the user's message.
4. Rule-based fallback -> if similarity is below a confidence threshold,
   a fallback intent responds instead of guessing incorrectly.

This design is intentionally simple and explainable — ideal for an
academic / portfolio project on chatbot design and basic NLP.
"""

from __future__ import annotations

import json
import logging
import random
import re
from pathlib import Path
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from config import CONFIDENCE_THRESHOLD
except ImportError:
    # Allows this module to be imported standalone (e.g. in isolated tests)
    # without requiring the top-level config.py to be on the path.
    CONFIDENCE_THRESHOLD = 0.20

logger = logging.getLogger(__name__)

# A small, hand-picked stopword list keeps this dependency-free (no NLTK
# downloads required) while still removing common noise words.
STOPWORDS: set[str] = {
    "a", "an", "the", "is", "are", "am", "was", "were", "be", "been", "being",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their", "to", "of", "in", "on", "at",
    "for", "with", "about", "do", "does", "did", "can", "could", "will",
    "would", "should", "please", "and", "or", "but", "so", "this", "that",
}


class Chatbot:
    """Rule-based / TF-IDF NLP chatbot for handling customer service queries."""

    def __init__(self, intents_path: str) -> None:
        self.intents_path = Path(intents_path)
        self.intents: List[dict] = self._load_intents()

        self.patterns: List[str] = []
        self.pattern_tags: List[str] = []
        self.responses_by_tag: Dict[str, List[str]] = {}

        for intent in self.intents:
            tag = intent.get("tag")
            patterns = intent.get("patterns", [])
            responses = intent.get("responses", [])
            self.responses_by_tag[tag] = responses

            for pattern in patterns:
                self.patterns.append(self._preprocess(pattern))
                self.pattern_tags.append(tag)

        if not self.patterns:
            raise ValueError("No patterns found in intents file. Cannot build chatbot.")

        # Fit TF-IDF vectorizer once at startup (fast lookups afterwards).
        self.vectorizer = TfidfVectorizer()
        self.pattern_vectors = self.vectorizer.fit_transform(self.patterns)

        logger.info(
            "Chatbot initialized with %d intents and %d training patterns.",
            len(self.intents), len(self.patterns),
        )

    # ---------------------------------------------------------- #
    # Loading
    # ---------------------------------------------------------- #
    def _load_intents(self) -> List[dict]:
        if not self.intents_path.exists():
            raise FileNotFoundError(f"Intents file not found: {self.intents_path}")

        with open(self.intents_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        intents = data.get("intents", [])
        if not intents:
            raise ValueError("Intents file contains no 'intents' list.")

        return intents

    # ---------------------------------------------------------- #
    # Preprocessing
    # ---------------------------------------------------------- #
    @staticmethod
    def _preprocess(text: str) -> str:
        """Lowercase, strip punctuation/numbers noise, remove stopwords."""
        if not text:
            return ""

        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", " ", text)  # remove punctuation
        tokens = text.split()
        filtered = [t for t in tokens if t not in STOPWORDS]

        # Guard: if stopword removal strips everything, fall back to
        # the raw tokens so short greetings like "hi" are never lost.
        if not filtered:
            filtered = tokens

        return " ".join(filtered)

    # ---------------------------------------------------------- #
    # Core matching logic
    # ---------------------------------------------------------- #
    def get_intent_tag(self, user_input: str) -> str:
        """Returns the matched intent tag for the given input (or 'fallback').

        Exposed as its own method (rather than only bundled inside
        `get_response`) so that matching accuracy can be unit-tested
        independently of which random response text gets chosen.
        """
        if not user_input or not str(user_input).strip():
            return "fallback"

        cleaned = self._preprocess(str(user_input))
        if not cleaned:
            return "fallback"

        try:
            user_vector = self.vectorizer.transform([cleaned])
            similarities = cosine_similarity(user_vector, self.pattern_vectors)[0]

            best_idx = int(similarities.argmax())
            best_score = float(similarities[best_idx])
            best_tag = self.pattern_tags[best_idx]

            logger.info(
                "Input: %r -> Best match tag: %s (score=%.2f)",
                user_input, best_tag, best_score,
            )

            return best_tag if best_score >= CONFIDENCE_THRESHOLD else "fallback"

        except Exception as e:
            logger.error("Error while matching intent for %r: %s", user_input, e)
            return "fallback"

    def get_response(self, user_input: str) -> str:
        """Returns the best-matching response for the given user input."""
        fallback_responses = self.responses_by_tag.get(
            "fallback", ["Could you say that again?"]
        )

        tag = self.get_intent_tag(user_input)
        responses = self.responses_by_tag.get(tag) or fallback_responses

        if not responses:
            return "I'm sorry, I don't have a response for that right now."

        return random.choice(responses)