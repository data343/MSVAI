import os
import requests
import json
from langdetect import detect, LangDetectException

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

class ReportResponder:
    def __init__(self, api_key, style_guide_text, model_name="meta-llama/llama-4-scout"):
        """
        Initializes the ReportResponder.
        :param api_key: Your OpenRouter API key.
        :param style_guide_text: The content of the CEO reply style guide.
        :param model_name: The OpenRouter model name to use.
        """
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY must be provided.")
        
        self.api_key = api_key
        self.model_name = model_name
        
        # Combine style guide with base instructions for the system message
        # The core instructions for the LLM are now part of this system message.
        self.system_message_content = f"""Your primary instruction is to follow the CEO's reply style detailed below:
--- CEO Reply Style Guide ---
{style_guide_text}
--- End CEO Reply Style Guide ---

Based *strictly* on the CEO's style guide above, your task is to write a reply to an employee's weekly report.
The reply should generally:
1. Acknowledge receipt of the report.
2. Briefly mention a key point or focus from the report.
3. If appropriate for the CEO's style, ask a brief question about next steps for that key point.

IMPORTANT:
- Adhere *strictly* to the "General Prompt for LLM" and the "Examples of My Replies" from the CEO's style guide.
- The reply MUST be very short and professional.
- Do NOT use formal salutations like "Уважаемый коллега," or "Dear colleague,".
- Do NOT use formal closings like "С уважением," or "Sincerely,".
- Directly start with the substance of the reply as shown in the examples.
"""

    def generate_reply(self, report_text):
        """
        Generates a personalized reply for a given report text.
        """
        detected_lang = "ru" # Default language
        try:
            detected_lang = detect(report_text)
        except LangDetectException:
            print(f"Warning: Language detection failed for report. Defaulting to English for LLM instructions.")
            # Fallback or more general instruction if detection fails
            detected_lang = "en" # Or handle as unknown

        language_instruction = f"The report is written in {detected_lang}. Please write your reply in {detected_lang}."
        if detected_lang == 'uk':
            language_instruction = "Звіт написаний українською. Будь ласка, напиши свою відповідь українською мовою."
        elif detected_lang == 'ru':
            language_instruction = "Отчет написан на русском. Пожалуйста, напиши свой ответ на русском языке."
        # Add more languages as needed or make it more generic:
        # else:
        # language_instruction = f"The report is written in an undetermined language (detected code: {detected_lang}). Please reply in the same language if possible, or English."


        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Construct messages for the API
        # The user message now primarily contains the report and the dynamic language instruction.
        messages = [
            {"role": "system", "content": self.system_message_content},
            {"role": "user", "content": f"{language_instruction}\n\nEmployee's Report:\n---\n{report_text}\n---"}
        ]
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7 # Adjust creativity as needed
        }

        try:
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=90) # Increased timeout
            response.raise_for_status()  # Raise an exception for bad status codes
            
            response_json = response.json()
            if response_json.get("choices") and len(response_json["choices"]) > 0:
                reply = response_json["choices"][0].get("message", {}).get("content", "")
                return reply.strip()
            else:
                error_detail = response_json.get("error", {}).get("message", "Unknown error structure.")
                print(f"LLM API Error: Unexpected response structure: {response_json}")
                return f"Error: LLM did not return a valid reply. Details: {error_detail}"

        except requests.exceptions.RequestException as e:
            print(f"LLM API Error: Could not connect to OpenRouter: {e}")
            return f"Error: Could not connect to LLM API. Details: {e}"
        except json.JSONDecodeError:
            print(f"LLM API Error: Could not decode JSON response: {response.text}")
            return f"Error: Invalid response from LLM API."
        except Exception as e:
            print(f"LLM API Error: An unexpected error occurred: {e}")
            return f"Error: An unexpected error occurred during LLM communication. Details: {e}"

if __name__ == "__main__":
    # This part is for testing the ReportResponder class directly if needed.
    # It's not called by check_weekly_reports.py anymore.
    print("Testing ReportResponder class...")

    mock_style_guide = """# CEO Reply Style Guide
## General Prompt for LLM
Speak politely, specifically, professionally, and be very short.
## Examples of My Replies
**Example 1:**
Report: "Focused on X."
My Reply: "Thanks. Good focus on X. Next steps?"
"""
    
    api_key_test = os.environ.get("OPENROUTER_API_KEY")
    if not api_key_test:
        print("OPENROUTER_API_KEY environment variable not set. Cannot run test.")
    else:
        responder = ReportResponder(api_key=api_key_test, style_guide_text=mock_style_guide)
        
        test_report_en = "This week, my main focus was on finalizing the Q3 budget. I also started preliminary research for the new marketing campaign."
        print(f"\n--- Test Report (EN) ---\n{test_report_en}")
        reply_en = responder.generate_reply(test_report_en)
        print(f"\n--- LLM Reply (EN) ---\n{reply_en}")

        test_report_uk = "Цього тижня головним фокусом була підготовка квартального звіту. Також розпочав аналіз конкурентів для нового продукту."
        print(f"\n--- Test Report (UK) ---\n{test_report_uk}")
        reply_uk = responder.generate_reply(test_report_uk)
        print(f"\n--- LLM Reply (UK) ---\n{reply_uk}")

        test_report_ru = "Привет, на этой неделе я в основном занимался важными делами и не очень, вероятно буду думать про шиладжит, но работать над чтением импорт бабл. Как у тебя дела?"
        print(f"\n--- Test Report (RU) ---\n{test_report_ru}")
        reply_ru = responder.generate_reply(test_report_ru)
        print(f"\n--- LLM Reply (RU) ---\n{reply_ru}")

        test_report_mixed = "Main focus: підготовка звіту. Also worked on some other tasks."
        print(f"\n--- Test Report (Mixed) ---\n{test_report_mixed}")
        reply_mixed = responder.generate_reply(test_report_mixed)
        print(f"\n--- LLM Reply (Mixed) ---\n{reply_mixed}")

    # To run this test (optional):
    # 1. Make sure OPENROUTER_API_KEY is set in your environment.
    # 2. Run `python jobs/generate_report_reply.py` from your terminal (with venv activated).
