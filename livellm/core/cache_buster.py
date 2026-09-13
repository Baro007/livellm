"""
LiveLLM - Cache Buster Module
Prevents inference providers from artificially suppressing TTFT using Prompt Caching.
Injects unique cryptographic / UUID nonces into the prompt header.
"""

import uuid
from typing import Dict, Any, List


def generate_nonce() -> str:
    """Generate a high-entropy UUID4 nonce."""
    return str(uuid.uuid4())


def inject_cache_buster(prompt: str, nonce: str | None = None) -> str:
    """
    Prepends a unique nonce header to the user prompt.
    Forces the provider's prefill engine to process the tokens afresh without hitting cache.
    """
    if nonce is None:
        nonce = generate_nonce()
    return f"[Nonce: {nonce}]\n{prompt}"


def wrap_messages_with_nonce(messages: List[Dict[str, Any]], nonce: str | None = None) -> List[Dict[str, Any]]:
    """
    Applies cache busting to a chat messages list.
    Injects nonce into the first user message or system message.
    """
    if nonce is None:
        nonce = generate_nonce()

    new_messages = [msg.copy() for msg in messages]
    if not new_messages:
        return [{"role": "user", "content": f"[Nonce: {nonce}]"}]

    first_msg = new_messages[0]
    content = first_msg.get("content", "")
    if isinstance(content, str):
        first_msg["content"] = f"[ProbeNonce: {nonce}]\n{content}"
    return new_messages
