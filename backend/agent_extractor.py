# File: agent_extractor.py

from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage
# --- CHANGE: Import the base ChatModel class for more flexible type hinting ---
from langchain_core.language_models.chat_models import BaseChatModel
from PIL import Image
import io
import base64


# In a larger project, this AppState could be in a shared types.py file
class AppState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    health_issue: str
    extracted_text: str
    image_path: str


class DataExtractorAgent:
    """Agent 0: Extracts text from a medical report image."""

    # --- CHANGE: Accept any LangChain chat model, including Gemini or Ollama ---
    def __init__(self, model: BaseChatModel):
        self.model = model

    def __call__(self, state: AppState):
        print("---AGENT 0: Data Extractor---")

        image_path = state.get("image_path")

        if not image_path:
            return {"extracted_text": "Error: No image path provided to the extractor agent."}

        try:
            # Open the image and convert to a base64 string for the model
            with Image.open(image_path) as img:
                buffer = io.BytesIO()
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(buffer, format="PNG")
                img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # Use the standard HumanMessage format for multimodal input
            extraction_prompt = """
            Your task is to act as an Optical Character Recognition (OCR) engine.
            Transcribe the text from the provided medical report image.
            - Be as accurate as possible.
            - Preserve the original formatting.
            - Do not add any commentary or analysis.
            - If the image is unreadable or contains no text, respond with only the phrase: "[UNREADABLE_IMAGE]".
            """

            message = HumanMessage(
                content=[
                    {"type": "text", "text": extraction_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_base64}"},
                    },
                ]
            )

            response = self.model.invoke([message])
            extracted_text = response.content

            print("---AGENT 0: Successfully extracted text from image.---")
            return {"extracted_text": extracted_text}

        except FileNotFoundError:
            print(f"Error: Image file not found at {image_path}")
            return {"extracted_text": f"Error: Image file not found at {image_path}"}
        except Exception as e:
            print(f"An error occurred during text extraction: {e}")
            return {"extracted_text": f"An unexpected error occurred: {e}"}

