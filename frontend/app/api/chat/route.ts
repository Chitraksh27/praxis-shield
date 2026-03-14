import { streamText, convertToModelMessages } from 'ai'; 
import { createOpenAI } from '@ai-sdk/openai';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';

const localOllama = createOpenAI({
  baseURL: 'http://127.0.0.1:11434/v1',
  apiKey: 'dummy-key-ignored', 
});

export async function POST(req: Request) {
  const { messages } = await req.json();

  const lastUserMessage = messages[messages.length - 1];
  const textPart = lastUserMessage.parts?.find((p: any) => p.type === 'text');
  const rawText = textPart ? textPart.text : '';

  const transport = new SSEClientTransport(new URL('http://127.0.0.1:8000/sse'));
  const client = new Client(
    { name: 'nextjs-hard-proxy', version: '1.0.0' },
    { capabilities: {} }
  );
  await client.connect(transport);

  // REDACTION PROXY
  const response = await client.callTool({
    name: 'anonymize_patient_data',
    arguments: { text: rawText } 
  });
  
  const mcpResponse = response as any;
  const scrubbedText = mcpResponse.content[0].text;

  // OVERWRITE ORIGINAL TEXT
  if (textPart) {
    textPart.text = scrubbedText;
  }

  // 1. EXTRACT THE AWAIT TO FIX THE PROMISE ERROR
  const modelMessages = await convertToModelMessages(messages);

  const result = await streamText({
    model: localOllama('hipaa-llama'), 
    // Pass the resolved array directly
    messages: modelMessages,
    system: `You are a specialized Clinical Decision Support System (CDSS) for healthcare professionals. 
Your task is to analyze the provided redacted EHR data and summarize clinical findings. 
The input has been HIPAA-redacted by a secure proxy; it contains no PII/PHI. 
Identify potential patterns, suggest clinical documentation improvements, and summarize 
the patient's history as presented. Do not provide a diagnosis to a patient; 
provide professional technical analysis to a clinician. Strictly adhere to the provided data. If information (like lab results or demographics) is marked as [REDACTED] or is missing, acknowledge it as unavailable rather than speculating.`,
  });

  // 2. USE THE V6 UI PROTOCOL SO THE FRONTEND CAN READ IT
  return result.toUIMessageStreamResponse();
}