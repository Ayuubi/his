from openai import OpenAI, OpenAIError
import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def ask_gpt(messages):
    """
    Ask ChatGPT with full conversation messages
    """
    import json

    if isinstance(messages, str):
        messages = json.loads(messages)  # frappe sends list as JSON string

    api_key = frappe.db.get_single_value('ChatGPT Seetings', 'api')
    if not api_key:
        frappe.throw(_("API key not found! Configure your API key in ChatGPT Settings."))

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or gpt-4 if you have access
            messages=messages,
            max_tokens=512,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except OpenAIError as e:
        error_msg = str(e)
        frappe.log_error(error_msg, "ChatGPT Integration Error")
        if "insufficient_quota" in error_msg or "429" in error_msg:
            return _("⚠️ Your OpenAI quota is exhausted. Check billing.")
        return _("⚠️ OpenAI service unavailable. Try again later.")
