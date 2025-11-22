import os
import google.generativeai as genai
from django.conf import settings
from typing import Dict, List, Optional
import json
import random

# Define safety settings to allow responses
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

class GeminiService:
    """Ultimate service for detailed, human-like, data-rich responses"""

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Keeping the model name as requested
        self.model_name = "gemini-2.0-flash"
        self.conversation_history = {}

    def classify_intent(self, query: str) -> str:
        """Classify user query intent"""
        intent_prompt = f"""Classify this banking query into ONE intent:
- transaction_analysis: spending/expenses questions
- investment_overview: portfolio/returns questions
- recommendation: seeking advice
- general_query: other questions
- summary: financial overview requests

Query: {query}

Intent (one word):"""

        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                intent_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.1),
                safety_settings=SAFETY_SETTINGS
            )

            if response.parts:
                return response.text.strip().lower()
            return "general_query"

        except Exception as e:
            print(f"Intent error: {e}")
            return "general_query"

    def generate_response(
        self,
        user_query: str,
        customer_profile: Dict,
        context_data: Dict,
        conversation_history: List[Dict] = None,
        previous_thought_signature: Optional[str] = None
    ) -> Dict:
        """Generate detailed, data-rich AI response"""

        system_prompt = self._build_detailed_prompt(customer_profile, context_data)

        chat_history = []
        is_first_message = not conversation_history or len(conversation_history) <= 1

        if conversation_history:
            for msg in conversation_history[-8:]:
                role = "user" if msg['role'] == 'user' else "model"
                chat_history.append({'role': role, 'parts': [msg['content']]})

        # Adjust instructions based on conversation history
        if is_first_message:
            instruction = "Start with a friendly welcome to the user by name."
        else:
            instruction = "Jump straight into the answer. Do NOT greet the user again."

        current_query = f"""{system_prompt}

User: {user_query}

INSTRUCTIONS FOR ARYA:
- **{instruction}**
- **Conversational Flow**: Write in natural paragraphs, not just lists. Tell a story with the data.
- **Be Detailed**: Go beyond simple answers. Provide numbers, percentages, comparisons, and insights.
- **Use the Data**: Your answer MUST be grounded in the provided financial data. Mention specific transactions or investments.
- **Human Tone**: Write like a real, friendly financial expert. Use contractions, casual language, and be encouraging.
- **Structure**: You can use bullet points for lists of numbers, but wrap them in conversational text.
- **Proactive Advice**: Always end with a valuable insight or a thoughtful question to guide the user.

Arya's Detailed Response:"""

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=800,
                    top_p=0.95,
                ),
                safety_settings=SAFETY_SETTINGS
            )

            if chat_history:
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(current_query)
            else:
                response = model.generate_content(current_query)

            if response.parts:
                response_text = self._humanize_response(response.text)
            else:
                response_text = "I'm having trouble thinking of a detailed response. Could you ask differently?"

            return {
                'response': response_text,
                'thought_signature': None,
                'model_used': self.model_name
            }

        except Exception as e:
            print(f"Gemini error: {e}")
            return {'response': "Oops, technical glitch! 😅 Try again in a moment.", 'error': str(e)}

    def _build_detailed_prompt(self, customer_profile: Dict, context_data: Dict) -> str:
        """Build a comprehensive, data-rich prompt for the model"""

        name = customer_profile.get('name', 'there')

        prompt = f"""You are Arya, a top-tier financial analyst and relationship manager at SmartBank. Your goal is to provide deep, data-driven insights in a friendly, human way.

CUSTOMER PROFILE:
- Name: {name}
- Age: {customer_profile.get('age')}
- Risk Tolerance: {customer_profile.get('risk_level', 'Not set').title()}
- Annual Income: ₹{customer_profile.get('annual_income', 0):,.0f}
- Financial Goals: {customer_profile.get('financial_goals', 'Not set').replace('_', ' ').title()}

---
FINANCIAL DATA SNAPSHOT
---
"""

        # Add Detailed Transaction Data
        if context_data.get('transactions'):
            prompt += "\nRECENT TRANSACTIONS (Sample of up to 10):\n"
            for t in context_data['transactions'][:10]:
                prompt += f"- {t['date']}: {t['merchant']} ({t['category']}) - ₹{t['amount']:,.0f}\n"

        # Add Detailed Investment Data
        if context_data.get('investments'):
            prompt += "\nINVESTMENT HOLDINGS:\n"
            for i in context_data['investments']:
                prompt += f"- {i['product_name']} ({i['product_type']}): Invested ₹{i['invested_amount']:,.0f}, now worth ₹{i['current_value']:,.0f} ({i['returns_percentage']:+.2f}% return)\n"

        prompt += "\n--- END OF DATA ---"

        return prompt

    def _humanize_response(self, response: str) -> str:
        """Make the response sound more natural"""
        return response.strip()

    def generate_follow_up_suggestions(self, intent: str, context: Dict = None) -> List[str]:
        """Generate more insightful follow-up suggestions"""

        all_suggestions = {
            'transaction_analysis': [
                "Break down my spending by category",
                "Were there any large, one-time expenses?",
                "How does my spending compare to my income?",
            ],
            'investment_overview': [
                "Which investment has the highest return?",
                "What's the risk level of my overall portfolio?",
                "Tell me more about my worst-performing asset.",
            ],
            'recommendation': [
                "Based on my risk profile, what should I buy next?",
                "I have ₹50,000 to invest, what do you suggest?",
                "How can I better align my portfolio with my goals?",
            ],
            'summary': [
                "Give me a detailed financial health report.",
                "What are the top 3 insights from my data?",
                "Summarize my financial situation in one paragraph.",
            ],
            'general_query': [
                "Analyze my spending habits.",
                "Give me a deep dive into my investments.",
                "What's one thing I could do better financially?",
            ]
        }

        suggestions = all_suggestions.get(intent, all_suggestions['general_query'])
        return random.sample(suggestions, min(3, len(suggestions)))
