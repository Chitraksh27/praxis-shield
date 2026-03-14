import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Set your Groq API key here or in your environment variables
client = Groq(api_key=os.getenv("GROQ_API_KEY", "your-groq-api-key-here"))

# The instruction is constant for the fine-tuning task
INSTRUCTION = "You are a specialized Clinical Decision Support System (CDSS). Analyze the provided redacted EHR data. Identify potential patterns, suggest clinical documentation improvements, and summarize the patient's history. Do not provide a diagnosis to a patient; provide professional technical analysis to a clinician."

def generate_synthetic_batch(batch_size=5):
    prompt = f"""
    You are an expert medical data generator. Generate {batch_size} highly diverse, highly realistic 
    Electronic Health Record (EHR) notes and their corresponding expert clinical summaries.
    
    CRITICAL RULES:
    1. The EHR data MUST contain [REDACTED] tags for names, locations, and facilities.
    2. Vary the medical conditions wildly (e.g., cardiology, trauma, endocrinology, psychiatry).
    3. The 'output' must be a structured, professional Markdown summary with a Chain-of-Thought approach.
    
    Respond STRICTLY in JSON format matching this schema:
    {{
      "records": [
        {{
          "input": "The raw, messy, redacted EHR text.",
          "output": "The perfect, structured clinical summary."
        }}
      ]
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.8, # Slightly higher temperature for dataset diversity
    )
    
    return json.loads(response.choices[0].message.content)

def build_dataset(total_target=500, batch_size=5):
    dataset_file = "unsloth_medical_dataset.jsonl"
    iterations = total_target // batch_size
    
    print(f"Starting generation of {total_target} records using Groq 70B...")
    
    with open(dataset_file, "a", encoding="utf-8") as f:
        for i in range(iterations):
            try:
                print(f"Generating batch {i+1}/{iterations}...")
                data = generate_synthetic_batch(batch_size)
                
                for record in data.get("records", []):
                    # Format strictly for Unsloth/Alpaca
                    alpaca_row = {
                        "instruction": INSTRUCTION,
                        "input": record["input"],
                        "output": record["output"]
                    }
                    f.write(json.dumps(alpaca_row) + "\n")
                    
            except Exception as e:
                print(f"Error on batch {i+1}: {e}")
                
    print(f"Success! Dataset saved to {dataset_file}")

if __name__ == "__main__":
    build_dataset(total_target=500, batch_size=5)