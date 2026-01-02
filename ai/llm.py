import json
import logging

from openai import OpenAI

from chatbot_conf.settings import OPENAI_API_KEY

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are a CONTEXT-BOUND reasoning assistant.

You may ONLY use the information present in the CONTEXT.
You ARE allowed to logically reason over that context to answer the question.
You are NOT allowed to use outside knowledge.

Rules:
- If the answer can be reasonably determined from the context, return the most specific answer supported by it.
- If the answer cannot be determined, return exactly:
I don't know based on the provided context.

Output format:
Return a single valid JSON object with this exact shape:
{"response": "<your answer>"}

No markdown. No explanations. No extra keys.
"""

def ask_llm(context: str, question: str):
    """
    Send context and question to LLM, return structured response.

    Returns:
        tuple: (response_dict, usage_object)
            - response_dict has key "response" with the answer
            - usage_object contains token counts (or None on error)
    """
    if not context or not context.strip():
        return {"response": "I don't know based on the provided context."}, None

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{question}",
            },
        ],
    )

    model_response = response.choices[0].message.content
    usage = response.usage

    # Parse JSON response with fallback for malformed output
    try:
        json_response = json.loads(model_response)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON response, using raw text")
        json_response = {"response": model_response}

    return json_response, usage
