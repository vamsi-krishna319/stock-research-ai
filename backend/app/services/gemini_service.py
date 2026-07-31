# """
# Thin wrapper around Gemini chat models (via langchain-google-genai).

# Two models are exposed:
#     - flash: fast/cheap model used by individual specialist agents
#     - pro:   stronger model used for the final advisor + report synthesis
# """
# import json
# import logging

# from langchain_core.messages import HumanMessage, SystemMessage
# from langchain_google_genai import ChatGoogleGenerativeAI

# from app.config import settings

# logger = logging.getLogger(__name__)

# _flash_llm = None
# _pro_llm = None


# def get_flash_llm() -> ChatGoogleGenerativeAI:
#     global _flash_llm
#     if _flash_llm is None:
#         _flash_llm = ChatGoogleGenerativeAI(
#             model=settings.GEMINI_FLASH_MODEL,
#             google_api_key=settings.GEMINI_API_KEY,
#             temperature=0.3,
#         )
#     return _flash_llm


# def get_pro_llm() -> ChatGoogleGenerativeAI:
#     global _pro_llm
#     if _pro_llm is None:
#         _pro_llm = ChatGoogleGenerativeAI(
#             model=settings.GEMINI_PRO_MODEL,
#             google_api_key=settings.GEMINI_API_KEY,
#             temperature=0.4,
#         )
#     return _pro_llm


# def ask(system_prompt: str, user_prompt: str, use_pro: bool = False) -> str:
#     """Send a system+user prompt to Gemini and return raw text output."""
#     if not settings.GEMINI_API_KEY:
#         return (
#             "[Gemini API key not configured. Set GEMINI_API_KEY in your .env file "
#             "to enable AI-generated analysis.]"
#         )
#     llm = get_pro_llm() if use_pro else get_flash_llm()
#     try:
#         messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
#         response = llm.invoke(messages)
#         return response.content
#     except Exception as exc:  # noqa: BLE001
#         logger.exception("Gemini call failed")
#         return f"[Gemini call failed: {exc}]"


# def ask_json(system_prompt: str, user_prompt: str, use_pro: bool = False) -> dict:
#     """
#     Ask Gemini for a strictly-JSON response. Instructs the model to return
#     only JSON, then parses it defensively (stripping markdown fences if present).
#     """
#     strict_system = (
#         system_prompt
#         + "\n\nIMPORTANT: Respond with ONLY valid JSON. No markdown fences, "
#         "no commentary, no preamble."
#     )
#     raw = ask(strict_system, user_prompt, use_pro=use_pro)
#     cleaned = raw.strip()
#     if cleaned.startswith("```"):
#         cleaned = cleaned.strip("`")
#         if cleaned.lower().startswith("json"):
#             cleaned = cleaned[4:]
#     try:
#         return json.loads(cleaned)
#     except json.JSONDecodeError:
#         logger.warning("Failed to parse Gemini JSON output, returning raw text wrapper")
#         return {"raw_text": raw, "parse_error": True}


"""
Thin wrapper around Gemini chat models (via langchain-google-genai).

Two models are exposed:
    - flash: fast/cheap model used by individual specialist agents
    - pro:   stronger model used for the final advisor + report synthesis
"""
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import settings

logger = logging.getLogger(__name__)

_flash_llm = None
_pro_llm = None


def get_flash_llm() -> ChatGoogleGenerativeAI:
    global _flash_llm
    if _flash_llm is None:
        _flash_llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_FLASH_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
        )
    return _flash_llm


def get_pro_llm() -> ChatGoogleGenerativeAI:
    global _pro_llm
    if _pro_llm is None:
        _pro_llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_PRO_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.4,
        )
    return _pro_llm


def ask(system_prompt: str, user_prompt: str, use_pro: bool = False) -> str:
    """Send a system+user prompt to Gemini and return raw text output."""
    if not settings.GEMINI_API_KEY:
        return (
            "[Gemini API key not configured. Set GEMINI_API_KEY in your .env file "
            "to enable AI-generated analysis.]"
        )

    llm = get_pro_llm() if use_pro else get_flash_llm()

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = llm.invoke(messages)
        content = response.content

        # Gemini may return a list instead of a string
        if isinstance(content, list):
            parts = []

            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        parts.append(item.get("text", ""))
                else:
                    parts.append(str(item))

            return "\n".join(parts)

        return str(content)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini call failed")
        return f"[Gemini call failed: {exc}]"


def ask_json(system_prompt: str, user_prompt: str, use_pro: bool = False) -> dict:
    """
    Ask Gemini for a strictly-JSON response.
    """
    strict_system = (
        system_prompt
        + "\n\nIMPORTANT: Respond with ONLY valid JSON. "
        + "No markdown fences, no commentary, no preamble."
    )

    raw = ask(strict_system, user_prompt, use_pro=use_pro)

    cleaned = str(raw).strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        logger.warning(
            "Failed to parse Gemini JSON output. Raw output: %s",
            cleaned[:500],
        )
        return {
            "raw_text": cleaned,
            "parse_error": True,
        }