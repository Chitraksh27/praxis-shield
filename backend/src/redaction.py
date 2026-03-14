import json
import requests
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# --- 1. DETERMINISTIC PATTERNS (Score 1.0 overrides all SpaCy guessing) ---
mrn_pattern = Pattern(name="mrn_pattern", regex=r"\b\d{3}-\d{2}-\d{4}\b", score=1.0)
zip_pattern = Pattern(name="zip_pattern", regex=r"\b\d{5}\b", score=1.0)
us_phone_pattern = Pattern(name="us_phone", regex=r"\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", score=1.0)
aadhaar_pattern = Pattern(name="aadhaar_pattern", regex=r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", score=1.0)
pan_pattern = Pattern(name="pan_pattern", regex=r"\b[A-Z]{5}\d{4}[A-Z]\b", score=1.0)
pin_pattern = Pattern(name="pin_pattern", regex=r"\b[1-9]\d{5}\b", score=1.0)
ind_mobile_pattern = Pattern(name="ind_mobile_pattern", regex=r"\b(?:\+91[\s-]?)?[6789]\d{9}\b", score=1.0)
date_pattern = Pattern(name="date_pattern", regex=r"\b\d{2}[/-]\d{2}[/-]\d{4}\b", score=1.0)
address_pattern = Pattern(name="address_pattern", regex=r"(?i)\b(?:Flat|Apt|Apartment|Plot|Sector|Phase|Block)[\w\s\.,-]+?(?:Apartments?|Society|Complex|Tower|Building|Enclave|Nagar|Marg)\b", score=1.0)

custom_recognizers = [
    PatternRecognizer(supported_entity="MRN", patterns=[mrn_pattern]),
    PatternRecognizer(supported_entity="ZIP_CODE", patterns=[zip_pattern]),
    PatternRecognizer(supported_entity="PHONE_NUMBER", patterns=[us_phone_pattern]),
    PatternRecognizer(supported_entity="AADHAAR", patterns=[aadhaar_pattern]),
    PatternRecognizer(supported_entity="PAN_CARD", patterns=[pan_pattern]),
    PatternRecognizer(supported_entity="PIN_CODE", patterns=[pin_pattern]),
    PatternRecognizer(supported_entity="IND_PHONE", patterns=[ind_mobile_pattern]),
    PatternRecognizer(supported_entity="CUSTOM_DATE", patterns=[date_pattern]),
    PatternRecognizer(supported_entity="CUSTOM_ADDRESS", patterns=[address_pattern])
]

# --- 2. INITIALIZE ENGINES ---
analyzer = AnalyzerEngine()
for rec in custom_recognizers:
    analyzer.registry.add_recognizer(rec)
anonymizer = AnonymizerEngine()

def redact_text(raw_text: str) -> str:
    # --- PASS 1: THE HAMMER (Presidio + Custom Regex) ---
    # Threshold 0.85 protects medical terms. ORG is removed so Llama handles facilities.
    target_entities = [
        "PERSON", "LOCATION", "PHONE_NUMBER", "EMAIL_ADDRESS", 
        "MRN", "ZIP_CODE", "AADHAAR", "PAN_CARD", "PIN_CODE", "IND_PHONE", "CUSTOM_DATE", "CUSTOM_ADDRESS"
    ]
    
    results = analyzer.analyze(text=raw_text, entities=target_entities, language='en', score_threshold=0.85)
    operators = {entity: OperatorConfig("replace", {"new_value": "[REDACTED]"}) for entity in target_entities}
    
    presidio_scrubbed = anonymizer.anonymize(
        text=raw_text,
        analyzer_results=results,
        operators=operators
    ).text

    # --- PASS 2: THE SEMANTIC SCOUT (Llama 3.2 1B) ---
    prompt = f"""Analyze the medical text below and extract TWO things:
    1. Names of healthcare facilities (e.g., Hospitals, Clinics, ERs).
    2. Specific residential building names, street names, or apartment/flat numbers (e.g., "Flat 402", "Sunshine Apartments", "Kothrud").
    
    CRITICAL RESTRICTIONS: 
    - DO NOT extract medications (e.g., Albuterol, Furosemide, Metformin, Atorvastatin). 
    - DO NOT extract medical conditions or codes (e.g., COPD, NSTEMI). 
    - DO NOT extract broad states/regions like "Maharashtra" unless it is part of a specific street address.
    
    TEXT: "{presidio_scrubbed}"
    
    OUTPUT FORMAT: You must return a valid JSON object with a single key "entities" containing a list of strings.
    EXAMPLE: {{"entities": ["General Hospital", "Flat 4B", "Oakwood Complex"]}}
    """

    try:
        response = requests.post('http://127.0.0.1:11434/api/generate', json={
            "model": "llama3.2:1b", 
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.0}
        })
        
        # Safely parse the exact JSON schema
        data = json.loads(response.json()['response'])
        entities_to_redact = data.get("entities", [])
        
        # INTERROGATION HOOK: Print exactly what Llama thinks are facilities/addresses
        print(f"\n--- [DEBUG] LLAMA EXTRACTED ENTITIES: {entities_to_redact} ---\n")
        
        # --- PASS 3: THE EXECUTIONER ---
        final_text = presidio_scrubbed
        if isinstance(entities_to_redact, list):
            for entity in entities_to_redact:
                if len(entity) > 3: # Ignore stray acronyms or blank strings
                    final_text = final_text.replace(entity, "[REDACTED]")
                    
    except Exception as e:
        print(f"Ollama JSON extraction failed: {e}")
        final_text = presidio_scrubbed
        
    print(f"--- DEEP CLEANED PAYLOAD ---\n{final_text}\n------------------------")
    return final_text