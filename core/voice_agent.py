"""Voice Agent for PhysioAI Egypt.

Handles real-time bidirectional streaming over WebSockets to Gemini Live 3.8 / 2.0
with conversational Egyptian Arabic dialect and clinical safety gating.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional
import os

from config import (
    AUDIO_CHANNELS,
    AUDIO_SAMPLE_RATE,
    GEMINI_API_KEY,
    GEMINI_LIVE_MODEL,
    GEMINI_LIVE_URI,
    VOICE_AGENT_SYSTEM_PROMPT,
)

logger = logging.getLogger("VoiceAgent")


class GeminiLiveVoiceAgent:
    """Asynchronous client connecting to Gemini Live WebSockets for real-time Egyptian voice coaching."""

    SAFETY_TRIGGER_WORDS = [
        "وجع", "بيوجعني", "ألم", "دايخ", "دوخة", "مش قادر",
        "تعبان", "هموت", "وقف", "كفاية", "إصابة", "طقطقة"
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        system_instruction: str = VOICE_AGENT_SYSTEM_PROMPT,
        on_text_received: Optional[Callable[[str], None]] = None,
        on_safety_alert: Optional[Callable[[str], None]] = None,
    ):
        self.api_key = api_key or GEMINI_API_KEY
        self.system_instruction = system_instruction
        self.on_text_received = on_text_received
        self.on_safety_alert = on_safety_alert

        self.websocket = None
        self.is_connected = False
        self._receive_task: Optional[asyncio.Task] = None
        self.active_session_id: Optional[str] = None

    async def connect(self) -> bool:
        """Establishes WebSocket connection to Gemini Live bidirectional streaming endpoint."""
        if not self.api_key:
            logger.warning("Gemini API key is not configured. Voice agent running in offline mode.")
            return False

        try:
            import websockets
            uri_with_auth = f"{GEMINI_LIVE_URI}?key={self.api_key}"
            self.websocket = await websockets.connect(uri_with_auth)
            self.is_connected = True
            logger.info("Connected to Gemini Live endpoint.")

            # Send session configuration with Egyptian clinical prompt
            await self._send_initial_setup()

            # Start background message listener
            self._receive_task = asyncio.create_task(self._listen_loop())
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Gemini Live: {e}")
            self.is_connected = False
            return False

    async def _send_initial_setup(self) -> None:
        """Sends the initial setup configuration frame specifying audio modality and system instructions."""
        if not self.websocket:
            return

        setup_msg = {
            "setup": {
                "model": f"models/{GEMINI_LIVE_MODEL}",
                "generationConfig": {
                    "responseModalities": ["AUDIO", "TEXT"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": "Aoede"  # Warm, conversational prebuilt voice
                            }
                        }
                    }
                },
                "systemInstruction": {
                    "parts": [{"text": self.system_instruction}]
                }
            }
        }
        await self.websocket.send(json.dumps(setup_msg))

    async def send_audio_chunk(self, pcm_bytes: bytes) -> None:
        """Streams raw 16kHz PCM audio chunk to the Gemini Live session."""
        if not self.is_connected or not self.websocket:
            return

        import base64
        realtime_input = {
            "realtimeInput": {
                "mediaChunks": [
                    {
                        "mimeType": f"audio/pcm;rate={AUDIO_SAMPLE_RATE}",
                        "data": base64.b64encode(pcm_bytes).decode("utf-8")
                    }
                ]
            }
        }
        try:
            await self.websocket.send(json.dumps(realtime_input))
        except Exception as e:
            logger.error(f"Error sending audio chunk: {e}")

    async def send_exercise_context_event(self, rep_number: int, phase: str, angle: float) -> None:
        """Sends real-time biomechanical context cues so the Egyptian coach knows workout progress."""
        if not self.is_connected or not self.websocket:
            return

        cue_text = f"[حدث حركي]: المريض خلص العدة رقم {rep_number}، الزاوية الحالية {int(angle)} درجة، المرحلة: {phase}."
        text_msg = {
            "clientContent": {
                "turns": [
                    {
                        "role": "user",
                        "parts": [{"text": cue_text}]
                    }
                ],
                "turnComplete": True
            }
        }
        try:
            await self.websocket.send(json.dumps(text_msg))
        except Exception as e:
            logger.error(f"Error sending context cue: {e}")

    async def _listen_loop(self) -> None:
        """Listens for streaming response tokens, checks clinical safety rules, and routes responses."""
        try:
            while self.is_connected and self.websocket:
                raw_response = await self.websocket.recv()
                response_data = json.loads(raw_response)
                await self._handle_server_content(response_data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Voice agent listen loop error: {e}")
        finally:
            self.is_connected = False

    async def _handle_server_content(self, data: Dict[str, Any]) -> None:
        """Parses server payload for text parts and audio chunks."""
        server_content = data.get("serverContent", {})
        model_turn = server_content.get("modelTurn", {})
        parts = model_turn.get("parts", [])

        for part in parts:
            if "text" in part:
                text_content = part["text"]
                # Clinical safety interception
                self.check_safety_intercept(text_content)
                if self.on_text_received:
                    self.on_text_received(text_content)

    def check_safety_intercept(self, transcript: str) -> bool:
        """Deterministic safety rule checking for patient pain/distress signals."""
        for word in self.SAFETY_TRIGGER_WORDS:
            if word in transcript:
                logger.warning(f"Safety trigger intercepted: '{word}' in transcript.")
                if self.on_safety_alert:
                    self.on_safety_alert(f"تم إيقاف الجلسة فوراً لسلامتك! تم رصد إشارة ألم أو إجهاد ({word}).")
                return True
        return False

    async def close(self) -> None:
        """Gracefully cancels listener task and closes WebSocket connection."""
        self.is_connected = False
        if self._receive_task:
            self._receive_task.cancel()
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        logger.info("Voice agent session closed.")
