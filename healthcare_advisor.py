"""
MediVoice AI - Safe Healthcare Response Module
Provides safe, first-line, rule-based healthcare guidance in Malayalam and English.

Strict Healthcare Safety Rules:
1. NEVER diagnose an illness or disease.
2. NEVER prescribe medications or specify drug dosages.
3. ALWAYS prioritize emergency warning signs (chest pain, breathing trouble, etc.).
4. Provide only supportive measures (rest, hydration, monitoring).
5. ALWAYS advise consulting a qualified doctor for medical evaluation.
"""

import re
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# 1. EMERGENCY KEYWORDS & WARNING RESPONSES (HIGHEST PRIORITY)
# ---------------------------------------------------------------------------

EMERGENCY_KEYWORDS = {
    "en-IN": [
        "chest pain", "chest tightness", "heart attack", "cannot breathe",
        "can't breathe", "unable to breathe", "difficulty breathing",
        "trouble breathing", "hard to breathe", "struggling to breathe",
        "breathing problem", "breathing problems", "breathing issue",
        "breathing issues", "severe breathing", "shortness of breath",
        "breathless", "breathlessness", "unconscious", "passed out",
        "fainted", "sudden weakness", "paralysis", "stroke",
        "severe bleeding", "choking", "blue lips"
    ],
    "ml-IN": [
        "നെഞ്ചുവേദന", "നെഞ്ചിൽ വേദന", "നെഞ്ച് വേദന",
        "ശ്വാസതടസ്സം", "ശ്വാസംമുട്ടൽ", "ശ്വാസമെടുക്കാൻ ബുദ്ധിമുട്ട്",
        "ബോധക്ഷയം", "ബോധം നഷ്ടപ്പെട്ടു", "ബോധമില്ല",
        "പെട്ടെന്നുള്ള തളർച്ച", "കൈകാലുകൾ തളർന്നു", "പക്ഷാഘാതം",
        "കഠിനമായ രക്തസ്രാവം"
    ]
}

EMERGENCY_RESPONSES = {
    "en-IN": (
        "🚨 URGENT MEDICAL WARNING:\n"
        "The symptoms you described (such as chest pain, breathing difficulty, or sudden weakness) "
        "can be signs of a medical emergency.\n\n"
        "• Please seek immediate emergency medical care or call your local emergency ambulance service right now.\n"
        "• Do not attempt to drive yourself to the hospital.\n"
        "• If you are with someone, inform them immediately so they can assist you.\n\n"
        "⚠️ Disclaimer: MediVoice AI cannot provide emergency medical care. Please contact emergency services immediately."
    ),
    "ml-IN": (
        "🚨 അടിയന്തര മെഡിക്കൽ മുന്നറിയിപ്പ്:\n"
        "നിങ്ങൾ പറഞ്ഞ ലക്ഷണങ്ങൾ (നെഞ്ചുവേദന, ശ്വാസതടസ്സം, അല്ലെങ്കിൽ പെട്ടെന്നുള്ള തളർച്ച) "
        "അടിയന്തര വൈദ്യസഹായം ആവശ്യമുള്ള ഗുരുതരമായ അവസ്ഥയുടെ സൂചനയാകാം.\n\n"
        "• ദയവായി ഉടൻ തന്നെ അടുത്തുള്ള ആശുപത്രിയിലെ അത്യാഹിത വിഭാഗത്തിൽ (Emergency) ചികിത്സ തേടുക, "
        "അല്ലെങ്കിൽ ആംബുലൻസ് സർവീസിനെ വിളിക്കുക.\n"
        "• സ്വയം വാഹനം ഓടിച്ച് ആശുപത്രിയിൽ പോകാൻ ശ്രമിക്കരുത്.\n"
        "• കൂടെയുള്ളവരോട് വിവരം ഉടൻ പറയുക.\n\n"
        "⚠️ അറിയിപ്പ്: മെഡിവോയ്സ് എ.ഐ അടിയന്തര ചികിത്സ നൽകുന്നില്ല. ദയവായി ഉടൻ തന്നെ ഡോക്ടറെയോ അത്യാഹിത വിഭാഗത്തെയോ സമീപിക്കുക."
    )
}

# ---------------------------------------------------------------------------
# 2. COMMON SYMPTOM KEYWORDS & SUPPORTIVE GUIDANCE
# ---------------------------------------------------------------------------

# Symptoms keywords mapped to canonical symptom IDs
SYMPTOM_DEFINITIONS = {
    "headache": {
        "en": ["headache", "head pain", "head aches", "migraine"],
        "ml": ["തലവേദന", "തലവേദനയുണ്ട്", "തല വേദന", "തലവേദനയും"]
    },
    "fever": {
        "en": ["fever", "high temperature", "chills", "feeling hot"],
        "ml": ["പനി", "പനിയുണ്ട്", "പനിയാണ്", "ചൂട്", "പനിയും"]
    },
    "cough": {
        "en": ["cough", "coughing", "dry cough"],
        "ml": ["ചുമ", "ചുമയുണ്ട്", "ചുമയാണ്", "ചുമയും"]
    },
    "cold": {
        "en": ["cold", "runny nose", "sneezing", "congestion", "blocked nose"],
        "ml": ["ജലദോഷം", "ജലദോഷമുണ്ട്", "മൂക്കൊലിപ്പ്", "തുമ്മൽ", "ജലദോഷവും"]
    },
    "fatigue": {
        "en": ["fatigue", "tired", "tiredness", "exhaustion", "weakness", "body ache"],
        "ml": ["ക്ഷീണം", "ക്ഷീണമുണ്ട്", "ക്ഷീണമാണ്", "ക്ഷീണവും", "തളർച്ചയും", "ഉന്മേഷക്കുറവ്"]
    }
}

# General supportive advice for each symptom (English)
SYMPTOM_ADVICE_EN = {
    "headache": (
        "• For Headaches: Rest in a quiet, dark room, stay well-hydrated, and practice gentle relaxation. "
        "Limit screen time and bright lights."
    ),
    "fever": (
        "• For Fever: Drink plenty of fluids (water, soups, oral hydration), get adequate rest, and wear lightweight clothing. "
        "Monitor your body temperature regularly."
    ),
    "cough": (
        "• For Cough: Drink warm water, warm herbal tea, or warm broth. "
        "Steam inhalation and resting in an upright position can help soothe your throat."
    ),
    "cold": (
        "• For Cold: Stay warm, drink warm fluids, and get sufficient sleep. "
        "Gentle warm saline gargling or steam inhalation may relieve nasal and throat discomfort."
    ),
    "fatigue": (
        "• For Fatigue: Ensure you get adequate sleep (7–8 hours), drink enough water throughout the day, "
        "and have light, nutritious meals. Avoid heavy physical exertion."
    )
}

# General supportive advice for each symptom (Malayalam)
SYMPTOM_ADVICE_ML = {
    "headache": (
        "• തലവേദനയ്ക്ക്: വെളിച്ചവും ശബ്ദവും കുറഞ്ഞ മുറിയിൽ വിശ്രമിക്കുക. ആവശ്യത്തിന് വെള്ളം കുടിക്കുക. "
        "മൊബൈൽ, കമ്പ്യൂട്ടർ സ്ക്രീനുകൾ നോക്കുന്നത് ഒഴിവാക്കുക."
    ),
    "fever": (
        "• പനിക്ക്: ധാരാളം വെള്ളവും കഞ്ഞിവെള്ളവും കുടിക്കുക. ശരീരത്തിന് പൂർണ്ണ വിശ്രമം നൽകുക. "
        "ശരീര താപനില കൃത്യമായി നിരീക്ഷിക്കുക."
    ),
    "cough": (
        "• ചുമയ്ക്ക്: ചെറുചൂടുവെള്ളം കുടിക്കുക. ആവി പിടിക്കുന്നത് തൊണ്ടയിലെ അസ്വസ്ഥത കുറയ്ക്കാൻ സഹായിക്കും. "
        "തണുത്ത വെള്ളവും ആഹാരങ്ങളും ഒഴിവാക്കുക."
    ),
    "cold": (
        "• ജലദോഷത്തിന്: ചൂടുള്ള ദ്രവഭക്ഷണങ്ങൾ കഴിക്കുക, നല്ല വിശ്രമം എടുക്കുക. "
        "ഉപ്പുവെള്ളം കവിൾക്കൊള്ളുന്നതും ആവി പിടിക്കുന്നതും മൂക്കടപ്പിന് ആശ്വാസം നൽകും."
    ),
    "fatigue": (
        "• ക്ഷീണത്തിന്: ആവശ്യത്തിന് ഉറങ്ങുകയും വിശ്രമിക്കുകയും ചെയ്യുക. ധാരാളം വെള്ളം കുടിക്കുക, "
        "പോഷകസമൃദ്ധമായ ലഘുഭക്ഷണം കഴിക്കുക. കഠിനമായ അധ്വാനം ഒഴിവാക്കുക."
    )
}


# ---------------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def _detect_emergency(text_lower: str, language: str) -> bool:
    """
    Checks if the user query contains any emergency warning signs.
    Checks both the selected language list and the English list as a safeguard.
    """
    # Check language-specific keywords
    lang_key = "ml-IN" if language.startswith("ml") else "en-IN"
    for keyword in EMERGENCY_KEYWORDS.get(lang_key, []):
        if keyword in text_lower:
            return True

    # Also check English emergency keywords as a cross-language safeguard
    for keyword in EMERGENCY_KEYWORDS["en-IN"]:
        if keyword in text_lower:
            return True

    return False


def _detect_symptoms(text_lower: str) -> List[str]:
    """
    Identifies which common symptoms (headache, fever, cough, cold, fatigue)
    are present in the user query.
    """
    matched = []
    for symptom_id, keywords in SYMPTOM_DEFINITIONS.items():
        # Check both English and Malayalam keywords for broad matching
        all_keywords = keywords["en"] + keywords["ml"]
        for kw in all_keywords:
            if kw in text_lower:
                if symptom_id not in matched:
                    matched.append(symptom_id)
                break
    return matched


# ---------------------------------------------------------------------------
# 4. MAIN HEALTHCARE RESPONSE FUNCTION
# ---------------------------------------------------------------------------

def get_healthcare_response(query_text: str, language: str = "ml-IN") -> str:
    """
    Generates a safe, rule-based healthcare response based on user symptoms.

    Parameters:
        query_text (str): The patient's query or transcript text.
        language (str): Language code ("ml-IN" for Malayalam, "en-IN" for English).
                        Defaults to "ml-IN".

    Returns:
        str: Safe, non-diagnostic, supportive healthcare guidance.
    """
    # 1. Normalize language selection
    is_malayalam = str(language).lower().startswith("ml")
    lang_code = "ml-IN" if is_malayalam else "en-IN"

    # 2. Handle empty or whitespace-only input safely
    if not query_text or not isinstance(query_text, str) or not query_text.strip():
        if is_malayalam:
            return (
                "നിങ്ങളുടെ ആരോഗ്യ സംബന്ധമായ സംശയം വ്യക്തമായി പറയുക. "
                "(ഉദാഹരണത്തിന്: തലവേദന, പനി, ചുമ, ജലദോഷം, അല്ലെങ്കിൽ ക്ഷീണം)."
            )
        else:
            return (
                "Please describe your health query or symptoms clearly. "
                "(For example: headache, fever, cough, cold, or fatigue)."
            )

    text_lower = query_text.strip().lower()

    # 3. EMERGENCY SAFETY CHECK (HIGHEST PRIORITY)
    # Emergency signs override all standard symptom advice
    if _detect_emergency(text_lower, lang_code):
        return EMERGENCY_RESPONSES[lang_code]

    # 4. DETECT COMMON SYMPTOMS
    detected_symptoms = _detect_symptoms(text_lower)

    # 5. BUILD RESPONSE IF SYMPTOMS WERE DETECTED
    if detected_symptoms:
        if is_malayalam:
            # Malayalam Response Construction
            parts = [
                "ശ്രദ്ധിക്കുക: നിങ്ങൾ പറഞ്ഞ ലക്ഷണങ്ങൾക്കുള്ള പൊതുവായ ആരോഗ്യ വിവരങ്ങൾ താഴെ നൽകുന്നു:\n"
            ]
            for s in detected_symptoms:
                if s in SYMPTOM_ADVICE_ML:
                    parts.append(SYMPTOM_ADVICE_ML[s])

            parts.append(
                "\n⚠️ പ്രധാന മുന്നറിയിപ്പ്: ഈ വിവരങ്ങൾ പൊതുവായ അറിവിലേക്കായി മാത്രമുള്ളതാണ്. "
                "രോഗനിർണ്ണയത്തിനോ മരുന്നുകൾക്കോ പകരമല്ല. ലക്ഷണങ്ങൾ തുടരുകയാണെങ്കിലോ വർദ്ധിക്കുകയാണെങ്കിലോ "
                "ദയവായി ഒരു യോഗ്യതയുള്ള ഡോക്ടറെ കണ്ട് പരിശോധന നടത്തുക."
            )
            return "\n".join(parts)

        else:
            # English Response Construction
            parts = [
                "Here is general, safe supportive healthcare guidance based on your symptoms:\n"
            ]
            for s in detected_symptoms:
                if s in SYMPTOM_ADVICE_EN:
                    parts.append(SYMPTOM_ADVICE_EN[s])

            parts.append(
                "\n⚠️ Important Disclaimer: This guidance is for general information and comfort only. "
                "It does not provide medical diagnosis or prescriptions. If symptoms persist, worsen, "
                "or cause distress, please consult a qualified healthcare professional."
            )
            return "\n".join(parts)

    # 6. FALLBACK FOR GENERAL QUERIES WITHOUT MATCHED PREDEFINED SYMPTOMS
    if is_malayalam:
        return (
            "നിങ്ങൾ പറഞ്ഞ വിവരം മനസ്സിലാക്കി, എന്നാൽ നിർദ്ദിഷ്ട ലക്ഷണങ്ങൾ വ്യക്തമായി കണ്ടെത്താനായില്ല.\n\n"
            "• പൊതുവായ ആരോഗ്യത്തിനായി ധാരാളം വെള്ളം കുടിക്കുകയും നല്ല വിശ്രമം എടുക്കുകയും ചെയ്യുക.\n"
            "• നിങ്ങൾക്ക് ഏതെങ്കിലും തരത്തിലുള്ള ശാരീരിക അസ്വസ്ഥതകൾ അനുഭവപ്പെടുന്നുണ്ടെങ്കിൽ, "
            "ദയവായി ഒരു യോഗ്യതയുള്ള ഡോക്ടറുടെ സേവനം തേടുക.\n\n"
            "⚠️ അറിയിപ്പ്: മെഡിവോയ്സ് എ.ഐ രോഗനിർണ്ണയമോ മരുന്നുകളോ നിർദ്ദേശിക്കുന്നില്ല."
        )
    else:
        return (
            "Thank you for sharing your query, but no specific common symptoms from my list were identified.\n\n"
            "• For general wellbeing, ensure you get adequate rest and stay properly hydrated.\n"
            "• If you are experiencing any pain, discomfort, or ongoing health issues, "
            "please consult a qualified healthcare professional for a medical evaluation.\n\n"
            "⚠️ Notice: MediVoice AI provides general communication assistance and does not diagnose conditions or prescribe medications."
        )


# ---------------------------------------------------------------------------
# 5. STANDALONE TESTING BLOCK
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("--- MediVoice AI: Healthcare Advisor Module Test ---")

    # Example 1: Ordinary symptoms (Malayalam)
    query_ml = "എനിക്ക് ഇന്ന് ചെറിയ തലവേദനയും ക്ഷീണവും ഉണ്ട്"
    print("\n[Test 1 - Malayalam Ordinary Symptoms]:")
    print(f"Query: {query_ml}")
    print("Response:\n" + get_healthcare_response(query_ml, language="ml-IN"))

    # Example 2: Ordinary symptoms (English)
    query_en = "I have a cough and cold since yesterday"
    print("\n[Test 2 - English Ordinary Symptoms]:")
    print(f"Query: {query_en}")
    print("Response:\n" + get_healthcare_response(query_en, language="en-IN"))

    # Example 3: Emergency warning (Malayalam)
    emergency_ml = "എനിക്ക് പെട്ടെന്ന് കഠിനമായ നെഞ്ചുവേദന അനുഭവപ്പെടുന്നു"
    print("\n[Test 3 - Malayalam Emergency]:")
    print(f"Query: {emergency_ml}")
    print("Response:\n" + get_healthcare_response(emergency_ml, language="ml-IN"))

    # Example 4: Emergency warning (English)
    emergency_en = "My father has chest pain and difficulty breathing"
    print("\n[Test 4 - English Emergency]:")
    print(f"Query: {emergency_en}")
    print("Response:\n" + get_healthcare_response(emergency_en, language="en-IN"))

    # Example 5: Empty input
    print("\n[Test 5 - Empty Input]:")
    print(get_healthcare_response("", language="en-IN"))
