from __future__ import annotations

import logging

from app.agents.prompts.system import SYSTEM_PROMPT
from litellm import completion

logger = logging.getLogger(__name__)


def generate_business_wiki(yaml_text: str, model: str) -> str:
    logger.info("Generating business wiki", extra={"model": model, "yaml_chars": len(yaml_text)})
    response = completion(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Here is the employee Q&A YAML data. Read it and output the final Markdown only.\n\n"
                    f"```yaml\n{yaml_text}\n```"
                ),
            },
        ],
        temperature=0.0,
        max_tokens=16000,
        timeout=120,
    )
    logger.info("Response received")
    content = response["choices"][0]["message"]["content"]
    logger.debug("Response content length: %d chars", len(content))

    return content
