"use client";

import { useChat } from "@ai-sdk/react";
import { useState, useRef, useEffect } from "react";

export default function ChatPage() {
  // 1. Manually manage input state (Required in AI SDK v5+)
  const [input, setInput] = useState("");
  
  // 2. useChat now returns sendMessage and status instead of input/handleSubmit
  const { messages, sendMessage, status } = useChat();
  
  // 3. Derive loading state from the new status variable
  const isLoading = status === "submitted" || status === "streaming";
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom when new messages stream in
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 4. Custom submit handler to replace the deprecated handleSubmit
  const handleCustomSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    // Send the message using the new API format
    sendMessage({ text: input });
    
    // Clear the textarea manually
    setInput(""); 
  };

  // A helper function to submit the form via the textarea Enter key
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleCustomSubmit();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50 font-sans text-slate-900">
      
      {/* HEADER */}
      <header className="flex items-center justify-between p-4 bg-white border-b border-slate-200 shadow-sm z-10">
        <h1 className="text-xl font-bold text-slate-800">
          Praxis Shield <span className="text-sm font-normal text-slate-500 ml-2">Clinical Redaction Proxy</span>
        </h1>
        <div className="flex items-center space-x-2">
          <span className="flex h-3 w-3 rounded-full bg-emerald-500"></span>
          <span className="text-sm text-slate-600 font-medium">System Secure</span>
        </div>
      </header>

      {/* CHAT MESSAGES AREA */}
      <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-slate-500 space-y-4">
            <p className="text-lg font-medium">No clinical data loaded.</p>
            <p className="max-w-md">Paste a raw Electronic Health Record (EHR) database dump below to begin the deep-clean redaction process.</p>
          </div>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex w-full ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] md:max-w-[75%] rounded-2xl p-5 shadow-sm 
                whitespace-pre-wrap break-words leading-relaxed
                ${
                  m.role === "user"
                    ? "bg-blue-600 text-white rounded-br-sm"
                    : "bg-white border border-slate-200 text-slate-800 rounded-bl-sm"
                }`}
            >
              <div className={`text-xs font-bold mb-2 uppercase tracking-wider ${m.role === 'user' ? 'text-blue-200' : 'text-slate-400'}`}>
                {m.role === "user" ? "Raw Input Payload" : "Clinical AI"}
              </div>
              
              {/* Fallback to render raw content or new structured parts from AI SDK v5+ */}
              {m.parts ? m.parts.map((part, i) => part.type === 'text' ? <span key={i}>{part.text}</span> : null) : m.content}
            </div>
          </div>
        ))}
        
        {/* Loading Indicator */}
        {isLoading && (
           <div className="flex w-full justify-start">
             <div className="bg-white border border-slate-200 text-slate-500 rounded-2xl rounded-bl-sm p-4 shadow-sm flex items-center space-x-2">
               <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
               <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
               <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
               <span className="ml-2 text-sm font-medium">Redacting & Synthesizing...</span>
             </div>
           </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* INPUT FORM AREA */}
      <div className="p-4 bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-10">
        <div className="max-w-5xl mx-auto">
          <form
            onSubmit={handleCustomSubmit}
            className="relative flex items-end w-full space-x-4"
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Paste raw DB extract here... (Shift + Enter for new line)"
              className="flex-1 max-h-64 min-h-[60px] p-4 bg-slate-100 border-0 rounded-xl resize-y focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all whitespace-pre-wrap shadow-inner"
              rows={3}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-4 min-w-[120px] bg-blue-600 text-white font-bold rounded-xl hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-500/50 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors shadow-md"
            >
              Process
            </button>
          </form>
          <div className="mt-2 text-center">
            <span className="text-xs text-slate-400">
              HIPAA & DPDP Compliant Local Proxy. Data never leaves this device.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}