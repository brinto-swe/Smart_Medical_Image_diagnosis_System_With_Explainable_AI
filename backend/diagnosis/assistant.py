import os
import re
from typing import Any

from openai import OpenAI

from .models import ScanResult


BLOCKED_MEDICATION_TERMS = (
    "medicine",
    "drug",
    "tablet",
    "dose",
    "prescription",
    "antibiotic",
    "paracetamol",
    "ibuprofen",
    "acetaminophen",
    "amoxicillin",
)


def latest_scan_for_patient(user):
    return (
        ScanResult.objects.filter(patient=user)
        .select_related("patient", "uploaded_by")
        .order_by("-created_at")
        .first()
    )


def build_patient_context(user) -> dict[str, Any]:
    latest_scan = latest_scan_for_patient(user)
    explainability_note = ""
    if latest_scan and latest_scan.heatmap_image:
        explainability_note = (
            "A Grad-CAM heatmap is available and highlights the image regions the model relied on most."
        )

    return {
        "patient_name": user.full_name,
        "patient_id": user.patient_id or "",
        "age": user.age,
        "blood_type": user.blood_type or "",
        "primary_condition": user.primary_condition or "",
        "allergies": user.allergies or "",
        "latest_diagnosis_result": latest_scan.prediction if latest_scan else "",
        "latest_risk_level": latest_scan.risk_level if latest_scan else "",
        "latest_confidence": latest_scan.confidence if latest_scan else None,
        "latest_scan_type": latest_scan.scan_type if latest_scan else "",
        "latest_scan_date": latest_scan.created_at.isoformat() if latest_scan else "",
        "explainability_note": explainability_note,
    }


def blocked_term_found(text: str) -> bool:
    lowered = (text or "").lower()
    return any(term in lowered for term in BLOCKED_MEDICATION_TERMS)


def medication_advice_found(text: str) -> bool:
    lowered = (text or "").lower()
    if not blocked_term_found(lowered):
        return False
    allowed_refusals = (
        "cannot recommend",
        "can't recommend",
        "will not recommend",
        "do not recommend",
        "cannot suggest",
        "can't suggest",
        "will not suggest",
        "i cannot provide medication advice",
        "i can't provide medication advice",
        "ask your doctor about medication",
        "consult a clinician about medication",
    )
    if any(phrase in lowered for phrase in allowed_refusals):
        return False
    risky_patterns = (
        r"\b(take|use|start|try|continue|increase|decrease|combine|prescribe)\b.{0,50}\b("
        + "|".join(re.escape(term) for term in BLOCKED_MEDICATION_TERMS)
        + r")\b",
        r"\b\d+\s*(mg|ml|tablet|tablets|capsule|capsules|dose|doses)\b",
    )
    return any(re.search(pattern, lowered) for pattern in risky_patterns)


def patient_context_summary(context: dict[str, Any]) -> str:
    confidence = context.get("latest_confidence")
    confidence_text = ""
    if confidence not in (None, ""):
        value = float(confidence)
        if value <= 1:
            value *= 100
        confidence_text = f"{value:.1f}%"

    lines = [
        f"Patient name: {context.get('patient_name') or 'Unknown'}",
        f"Patient ID: {context.get('patient_id') or 'Unknown'}",
        f"Age: {context.get('age') or 'Unknown'}",
        f"Primary condition: {context.get('primary_condition') or 'Not provided'}",
        f"Allergies: {context.get('allergies') or 'Not provided'}",
        f"Latest diagnosis result: {context.get('latest_diagnosis_result') or 'No saved diagnosis yet'}",
        f"Latest risk level: {context.get('latest_risk_level') or 'Unknown'}",
        f"Latest confidence: {confidence_text or 'Unknown'}",
        f"Latest scan type: {context.get('latest_scan_type') or 'Unknown'}",
        f"Explainable AI note: {context.get('explainability_note') or 'No heatmap note available.'}",
    ]
    return "\n".join(lines)


def opening_message_for_patient(user) -> dict[str, Any]:
    context = build_patient_context(user)
    details = []
    if context["latest_diagnosis_result"]:
        confidence = context.get("latest_confidence")
        confidence_text = ""
        if confidence not in (None, ""):
            value = float(confidence)
            if value <= 1:
                value *= 100
            confidence_text = f" at {value:.1f}% confidence"
        details.append(
            f"I can already see your latest {context['latest_scan_type'] or 'medical image'} result: "
            f"{context['latest_diagnosis_result']} with {context['latest_risk_level'] or 'unknown'} risk{confidence_text}."
        )
    else:
        details.append("I do not see a saved diagnosis result yet, so we may need a little more context from you.")

    if context.get("explainability_note"):
        details.append(context["explainability_note"])

    question = (
        "Before we continue, please confirm your age and tell me whether you have any other health conditions, "
        "symptoms, or concerns you want me to consider. I can explain your report and help you understand warning "
        "signs, but I will not recommend medicines, prescriptions, or doses."
    )
    return {"reply": " ".join(details + [question]), "context": context}


def safe_medication_redirect(context: dict[str, Any]) -> str:
    result = context.get("latest_diagnosis_result") or "your latest report"
    risk = context.get("latest_risk_level") or "your current risk level"
    return (
        f"Based on {result} and {risk}, I can help explain what the report may mean, what symptoms are worth "
        "watching, and what questions you may want to ask your doctor. I cannot suggest medicines, drugs, tablets, "
        "doses, or prescriptions. If you want, ask me about the meaning of the result, the confidence level, the "
        "risk level, or the Grad-CAM heatmap."
    )


def local_contextual_reply(context: dict[str, Any], message: str) -> str:
    result = context.get("latest_diagnosis_result") or "your latest diagnosis result"
    risk = context.get("latest_risk_level") or "unknown"
    confidence = context.get("latest_confidence")
    confidence_text = "an unknown confidence score"
    if confidence not in (None, ""):
        value = float(confidence)
        if value <= 1:
            value *= 100
        confidence_text = f"{value:.1f}% confidence"

    age_text = f"age {context.get('age')}" if context.get("age") else "your age is not saved yet"
    condition = context.get("primary_condition") or "no saved long-term condition"
    lowered = (message or "").lower()

    if any(word in lowered for word in ("routine", "daily", "lifestyle", "sleep", "exercise", "walk", "activity")):
        focus = (
            "For a daily routine, keep the day gentle and predictable: sleep and wake at consistent times, take light "
            "walks if you feel well enough, avoid smoke and dusty environments, drink water regularly, and keep notes "
            "about cough, fever, breathing comfort, chest discomfort, and energy level. Because your saved result is "
            f"{result} with {risk} risk, avoid heavy exertion until a clinician reviews the report, and seek urgent "
            "care if breathing becomes difficult or symptoms worsen quickly."
        )
    elif any(word in lowered for word in ("food", "diet", "habit", "eat")):
        focus = (
            "For food habits, keep meals regular, choose more vegetables, fruits, whole grains, and lean protein, "
            "drink enough water, and reduce very salty, very sugary, and deep-fried foods."
        )
    elif "report" in lowered or "diagnosis" in lowered or "result" in lowered or "explain" in lowered:
        focus = (
            f"Your latest report is marked as {result}. The confidence value tells how strongly the AI matched this "
            "image to learned patterns, while the risk level helps decide how urgently the report should be reviewed. "
            "This is not a final clinical diagnosis by itself; it is a decision-support result for your doctor to "
            "interpret with symptoms, examination, and other tests."
        )
    elif "heatmap" in lowered or "grad" in lowered:
        focus = (
            "The Grad-CAM heatmap is an explainable AI view. Warmer regions show where the model paid more attention, "
            "so it helps a doctor review whether the model focused on medically relevant areas."
        )
    elif "risk" in lowered or "confidence" in lowered:
        focus = (
            "Risk level describes how much attention the result may need, while confidence describes how strongly the "
            "model matched its learned pattern. A confident model result still needs clinical review."
        )
    else:
        focus = "I can help you understand the result, symptoms to monitor, and questions to ask your doctor."

    return (
        f"Based on your saved context ({age_text}, primary condition: {condition}, latest result: {result}, "
        f"risk level: {risk}, {confidence_text}), here is a practical way to think about it. {focus} "
        "If you notice breathing difficulty, chest pain, high fever, worsening weakness, or symptoms that feel urgent, "
        "please contact a clinician quickly. I cannot provide medication, dose, or prescription advice."
    )


def ask_patient_assistant(user, message: str, conversation: list[dict[str, str]] | None = None) -> dict[str, Any]:
    context = build_patient_context(user)
    if blocked_term_found(message):
        return {"reply": safe_medication_redirect(context), "context": context}

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return {"reply": local_contextual_reply(context, message), "context": context, "source": "local_fallback"}

    model = os.environ.get("OPENAI_ASSISTANT_MODEL", "gpt-4.1-mini")
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are the intelligent assistant for a medical image diagnosis desktop application. "
        "Be warm, thoughtful, and specific. Use the patient context below when answering. "
        "If key details are missing, ask focused follow-up questions before giving a substantive explanation. "
        "Never recommend medicines, drugs, tablets, doses, prescriptions, or antibiotics. "
        "Do not name or suggest any medicine. Do not write like a canned script. "
        "You may explain diagnosis results, risk level, confidence level, what a Grad-CAM heatmap means, "
        "common warning signs to monitor, non-medication safety steps, and what questions to ask a clinician. "
        "Always avoid definitive diagnosis claims and remind the patient that clinical decisions belong to a licensed doctor.\n\n"
        f"Patient context:\n{patient_context_summary(context)}"
    )

    inputs = [{"role": "system", "content": system_prompt}]
    for item in (conversation or [])[-10:]:
        role = item.get("role", "")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            inputs.append({"role": role, "content": content})
    inputs.append({"role": "user", "content": message})

    try:
        response = client.responses.create(
            model=model,
            input=inputs,
            max_output_tokens=420,
        )
        reply = (response.output_text or "").strip()
    except Exception:
        reply = local_contextual_reply(context, message)

    if not reply:
        reply = "I'm sorry, I couldn't produce a clear answer just now. Please try asking the question a different way."

    if medication_advice_found(reply):
        reply = safe_medication_redirect(context)

    reply = re.sub(r"\s{3,}", "\n\n", reply).strip()
    return {"reply": reply, "context": context}
