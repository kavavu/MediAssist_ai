"""
AI-powered doctor response generation service.

Supports OpenAI, Kimi (Moonshot AI), and Google Gemini APIs.
Generates human-like, professional medical responses grounded in
the existing clinical engine output. Never independently diagnoses.
"""
import os
import random
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Prompt engineering — concise, grounded, safety-first
# ------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are an experienced, empathetic clinician drafting a response to a patient. "
    "You MUST NOT make a definitive diagnosis. You MUST NOT prescribe medication. "
    "You are only interpreting the output of an existing clinical screening tool. "
    "Write warmly, professionally, and concisely. Vary phrasing naturally. "
    "Always end with: 'This assessment is AI-assisted and not a final medical diagnosis.'"
)

_VARIATION_SEEDS = [
    "Use a calm, reassuring tone.",
    "Be slightly more formal and structured.",
    "Use warm, conversational language.",
    "Be concise and direct.",
    "Emphasize patient education gently.",
]


def _build_user_prompt(
    predicted_condition: Optional[str],
    severity: str,
    symptoms: str,
    urgency: str,
    recommended_tests: str,
    ai_insight: str,
    patient_message: Optional[str] = None,
) -> str:
    """Build a concise prompt grounded in clinical engine output."""
    seed = random.choice(_VARIATION_SEEDS)

    parts = [
        f"Clinical screening result: {predicted_condition or 'Unclear'}",
        f"Severity/priority: {severity}",
        f"Reported symptoms: {symptoms}",
        f"Urgency guidance: {urgency}",
        f"Recommended tests: {recommended_tests}",
        f"Clinical insight: {ai_insight}",
    ]
    if patient_message:
        parts.append(f"Patient message: {patient_message}")

    context = "\n".join(parts)

    return (
        f"{seed}\n\n"
        f"Based on the following clinical screening output, draft a professional, "
        f"empathetic doctor-style response for the patient.\n\n"
        f"{context}\n\n"
        f"Structure the response with these sections:\n"
        f"1. Acknowledgement — acknowledge their symptoms warmly.\n"
        f"2. Clinical interpretation — explain the screening result in plain language.\n"
        f"3. Care recommendations — practical next steps.\n"
        f"4. Recommended tests — list the suggested investigations.\n"
        f"5. Urgency guidance — explain when to seek urgent care.\n"
        f"6. Follow-up recommendation — suggest when to return or follow up.\n\n"
        f"Rules:\n"
        f"- Do NOT prescribe specific drugs or dosages.\n"
        f"- Do NOT give a definitive diagnosis.\n"
        f"- Use cautious language ('suggestive of', 'consistent with', 'may indicate').\n"
        f"- Keep it under 300 words.\n"
        f"- End with the required disclaimer."
    )


# ------------------------------------------------------------------
# OpenAI Provider
# ------------------------------------------------------------------

_openai_client = None

def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI
        except ImportError:
            return None
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        _openai_client = OpenAI(api_key=api_key, timeout=30.0)
    return _openai_client


def _call_openai(messages, model, temperature=0.7, max_tokens=600):
    client = _get_openai_client()
    if not client:
        return None
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("[OpenAI] API call failed: %s", exc)
        return None


# ------------------------------------------------------------------
# Kimi (Moonshot AI) Provider
# ------------------------------------------------------------------

_kimi_client = None

def _get_kimi_client():
    global _kimi_client
    if _kimi_client is None:
        try:
            from openai import OpenAI
        except ImportError:
            return None
        api_key = os.getenv("KIMI_API_KEY")
        if not api_key:
            return None
        _kimi_client = OpenAI(
            api_key=api_key,
            base_url="https://api.moonshot.cn/v1",
            timeout=30.0,
        )
    return _kimi_client


def _call_kimi(messages, model, temperature=0.7, max_tokens=600):
    client = _get_kimi_client()
    if not client:
        return None
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("[Kimi] API call failed: %s", exc)
        return None


# ------------------------------------------------------------------
# Google Gemini Provider
# ------------------------------------------------------------------

_gemini_model = None

def _get_gemini_model():
    global _gemini_model
    if _gemini_model is None:
        try:
            import google.generativeai as genai
        except ImportError:
            logger.warning("[Gemini] google-generativeai package not installed.")
            return None
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        _gemini_model = genai.GenerativeModel(model_name)
    return _gemini_model


def _call_gemini(system_prompt, user_prompt, temperature=0.7):
    model = _get_gemini_model()
    if not model:
        return None
    try:
        # Gemini uses a different format — combine system + user
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": 600,
                "top_p": 0.95,
            },
        )
        return response.text.strip()
    except Exception as exc:
        logger.error("[Gemini] API call failed: %s", exc)
        return None


# ------------------------------------------------------------------
# Provider selection
# ------------------------------------------------------------------

def _get_active_provider():
    """Determine which AI provider to use."""
    provider = os.getenv("AI_PROVIDER", "openai").lower()
    
    if provider == "gemini":
        if os.getenv("GEMINI_API_KEY"):
            return "gemini"
        logger.warning("[Gemini] GEMINI_API_KEY not set, trying OpenAI fallback...")
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        return None
    
    if provider == "kimi":
        if os.getenv("KIMI_API_KEY"):
            return "kimi"
        logger.warning("[Kimi] KIMI_API_KEY not set, trying OpenAI fallback...")
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        return None
    
    if provider == "openai":
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        logger.warning("[OpenAI] OPENAI_API_KEY not set, trying Gemini fallback...")
        if os.getenv("GEMINI_API_KEY"):
            return "gemini"
        return None
    
    return None


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def generate_doctor_response(
    predicted_condition: Optional[str],
    severity: str,
    symptoms: str,
    urgency: str,
    recommended_tests: str,
    ai_insight: str,
    patient_message: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generate an AI-assisted doctor response.

    Returns {"response": str, "source": "openai" | "kimi" | "gemini" | "fallback"}
    """
    provider = _get_active_provider()
    
    if provider == "gemini":
        model_name = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    elif provider == "kimi":
        model_name = model or os.getenv("KIMI_MODEL", "moonshot-v1-8k")
    elif provider == "openai":
        model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    else:
        logger.info("[AI] No provider available — using fallback.")
        return {
            "response": _fallback_response(
                predicted_condition, severity, symptoms, urgency, recommended_tests, ai_insight
            ),
            "source": "fallback",
        }

    user_prompt = _build_user_prompt(
        predicted_condition=predicted_condition,
        severity=severity,
        symptoms=symptoms,
        urgency=urgency,
        recommended_tests=recommended_tests,
        ai_insight=ai_insight,
        patient_message=patient_message,
    )

    if provider == "gemini":
        response_text = _call_gemini(_SYSTEM_PROMPT, user_prompt)
        if response_text:
            logger.info("[Gemini] Response generated successfully (model=%s).", model_name)
            return {"response": response_text, "source": "gemini"}
    elif provider == "kimi":
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        response_text = _call_kimi(messages, model_name)
        if response_text:
            logger.info("[Kimi] Response generated successfully (model=%s).", model_name)
            return {"response": response_text, "source": "kimi"}
    elif provider == "openai":
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        response_text = _call_openai(messages, model_name)
        if response_text:
            logger.info("[OpenAI] Response generated successfully (model=%s).", model_name)
            return {"response": response_text, "source": "openai"}

    # If we get here, the API call failed
    logger.warning("[AI] %s API call failed — using fallback.", provider)
    return {
        "response": _fallback_response(
            predicted_condition, severity, symptoms, urgency, recommended_tests, ai_insight
        ),
        "source": "fallback",
    }


def _fallback_response(
    predicted_condition: Optional[str],
    severity: str,
    symptoms: str,
    urgency: str,
    recommended_tests: str,
    ai_insight: str,
) -> str:
    """Structured fallback when AI APIs are unavailable."""
    condition = predicted_condition or "an unclear clinical picture"

    acknowledgements = [
        f"Thank you for reaching out. I have reviewed your symptoms ({symptoms}) and understand your concerns.",
        f"I appreciate you sharing your symptoms with us. I have carefully reviewed your report of {symptoms}.",
        f"Thank you for providing those details. I have noted your symptoms: {symptoms}.",
    ]

    interpretations = [
        f"Based on your reported symptoms, the clinical screening suggests a picture consistent with {condition}. This is an initial assessment and further evaluation is needed.",
        f"Your symptom pattern is suggestive of {condition}. However, this is a preliminary interpretation and not a definitive diagnosis.",
        f"The screening tool indicates that your symptoms align with {condition}. I would like to evaluate this further with you.",
    ]

    care_notes = [
        "Please rest, stay well-hydrated, and monitor your symptoms closely. Avoid self-medication until we complete the evaluation.",
        "I recommend adequate rest, good fluid intake, and careful symptom monitoring. Please do not start any medication without guidance.",
        "In the meantime, prioritize rest and hydration. Keep a symptom diary and note any changes.",
    ]

    return (
        f"{random.choice(acknowledgements)}\n\n"
        f"{random.choice(interpretations)}\n\n"
        f"{random.choice(care_notes)}\n\n"
        f"**Recommended Tests:**\n{recommended_tests}\n\n"
        f"**Urgency Guidance:**\n{urgency}\n\n"
        f"**Follow-up:**\n"
        f"Please schedule a follow-up after completing the recommended tests so we can review the results together and finalize your care plan.\n\n"
        f"---\n"
        f"*This assessment is AI-assisted and not a final medical diagnosis.*"
    )
