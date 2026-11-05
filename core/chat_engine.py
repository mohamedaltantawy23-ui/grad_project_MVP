"""Chatbot Engine for PhysioAI Egypt.

Provides a dedicated physiotherapy Q&A consultation interface powered by Gemini 2.5 / 1.5,
strictly constrained by system instructions to exercise rehabilitation and recovery guidance.
"""

import json
import logging
from typing import Dict, List, Optional
import os

from config import CHATBOT_SYSTEM_PROMPT, GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger("ChatEngine")


class PhysioChatEngine:
    """Physiotherapy-exclusive Gemini text assistant with conversation memory and clinical gating."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = GEMINI_MODEL,
        system_instruction: str = CHATBOT_SYSTEM_PROMPT,
    ):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.history: List[Dict[str, str]] = []
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """Initializes google-genai client if installed and API key is present."""
        if not self.api_key:
            logger.info("Chat engine initialized without API key (offline/mock mode active).")
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        except ImportError:
            # We can also use requests as a reliable fallback
            self._client = None

    def ask(self, user_question: str) -> str:
        """Sends user question to Gemini with physiotherapy clinical guardrails.

        Args:
            user_question: The patient's question in Arabic or English.

        Returns:
            Clinical guidance response string.
        """
        user_question = user_question.strip()
        if not user_question:
            return "من فضلك اكتب سؤالك أو استفسارك بخصوص التمارين أو العلاج الطبيعي."

        # Offline / Mock response mode when API key is missing
        if not self.api_key:
            return self._offline_consultation(user_question)

        try:
            if self._client:
                # Using google-genai SDK
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=user_question,
                    config={
                        "system_instruction": self.system_instruction,
                        "temperature": 0.4,
                    }
                )
                answer = response.text
            else:
                # Direct REST fallback via requests
                answer = self._rest_fallback_request(user_question)

            # Append to history
            self.history.append({"user": user_question, "assistant": answer})
            return answer

        except Exception as e:
            logger.error(f"Error communicating with Gemini Chat: {e}")
            return f"عذراً، حدث خطأ أثناء الاتصال بمساعد فيزيو: {e}. يرجى التحقق من اتصال الإنترنت ومفتاح الـ API."

    def _rest_fallback_request(self, question: str) -> str:
        """HTTP REST fallback to Gemini API without requiring SDK binary."""
        import requests

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": self.system_instruction}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": question}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 600
            }
        }
        res = requests.post(url, json=payload, timeout=15)
        res.raise_for_status()
        data = res.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def _offline_consultation(self, question: str) -> str:
        """Smart local guidance when running in offline mode without an active API key."""
        q_lower = question.lower()
        if any(w in q_lower for w in ["ألم", "وجع", "بيوجعني", "ركبة", "ركبتي"]):
            return (
                "📍 تنبيه طبي مهم: لو حسيت بألم حاد أو مفاجئ أثناء تمرين الركبة، "
                "وقف فوراً وريح المفصل. الوجع الطبيعي بيكون إجهاد عضلي بسيط فقط. "
                "إذا استمر الألم، ضروري تستشير دكتور العلاج الطبيعي المتابع لحالتك.\n\n"
                "(ملاحظة: هذا الرد استرشادي محلي. فعّل GEMINI_API_KEY للحصول على استجابات تفاعلية متقدمة)."
            )
        elif any(w in q_lower for w in ["سكوات", "قرفصاء", "squat"]):
            return (
                "💡 نصائح لأداء السكوات بطريقة آمنة:\n"
                "1. خلي رجليك باتساع الكتفين تقريباً.\n"
                "2. انزل بوزنك لورا كأنك بتقعد على كرسي، مع الحفاظ على ضهرك مفرود.\n"
                "3. اتأكد إن ركبتك ماتعديش صوابع رجلك وماتدخلش لجوه (Valgus).\n"
                "4. انزل لزاوية 90 إلى 100 درجة فقط لو حالتك تسمح بذلك."
            )
        else:
            return (
                "أهلاً بك في فيزيو-إيه آي! أنا هنا لمساعدتك في أي استفسار متعلق بتمارين التأهيل، "
                "صحة المفاصل والعضلات، وتصحيح وضعيات الجسم.\n\n"
                "📌 لتفعيل الردود الذكية الكاملة، يرجى كتابة مفتاح GEMINI_API_KEY داخل ملف .env."
            )

    def clear_history(self) -> None:
        """Clears the ongoing consultation history."""
        self.history.clear()
