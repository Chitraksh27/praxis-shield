from fastmcp import FastMCP
from redaction import redact_text

mcp = FastMCP("HIPAAShield")

@mcp.tool()
def anonymize_patient_data(text: str) -> str:
    """
    ALWAYS use this tool to redact Personally Identifiable Information (PII) and Protected Health Information (PHI) before answering questions about patients. Pass the raw text into this tool, and it will return the safe, redacted version.
    """
    return redact_text(text)

if __name__ == "__main__":
    mcp.run(transport = "sse")