import React, { useState, useRef, useEffect } from "react";
import { Send, Menu, X, Sparkles, Database } from "lucide-react";
import SchemaPanel from "../components/SchemaPanel";
import ChatMessage from "../components/ChatMessage";
import type { DbContext, Message } from "../types";
import { generateSqlAnalysis } from "../services/apiService";

const App: React.FC = () => {
  const [dbContext, setDbContext] = useState<DbContext>({
    connection: {
      host: "",
      port: 0,
      username: "",
      password: "",
      database: "",
      type: "PostgreSQL",
    },
    schema: "",
    selectedModel: "Gemini (Google)",
  });

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: `Hello! I'm your **SQL Analyst AI**. 

I can help you analyze your data by converting your questions into optimized SQL queries, explaining the logic, and suggesting visualizations.

To get started:
1.  **Configure your Database** in the sidebar (Host, User, DB Name).
2.  **Provide Schema Context** (Paste your CREATE TABLE statements).
3.  **Ask a question** about your data.

*Example: "Show total sales per month for the last year"*`,
      timestamp: new Date(),
    },
  ]);

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Mobile sidebar toggle
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Call Gemini API
    const responseText = await generateSqlAnalysis(
      userMessage.content,
      dbContext,
    );

    const botMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: responseText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, botMessage]);
    setIsLoading(false);
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar - Desktop */}
      <SchemaPanel
        dbContext={dbContext}
        setDbContext={setDbContext}
        isOpen={true}
      />

      {/* Sidebar - Mobile Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        >
          <div
            className="absolute left-0 top-0 h-full bg-white shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <SchemaPanel
              dbContext={dbContext}
              setDbContext={setDbContext}
              isOpen={true}
            />
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="absolute top-4 right-4 p-2 text-slate-500"
            >
              <X size={24} />
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <button
              className="md:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
              onClick={() => setIsSidebarOpen(true)}
            >
              <Menu size={24} />
            </button>
            <div className="flex items-center gap-2 text-indigo-600">
              <Sparkles className="w-6 h-6" />
              <h1 className="font-bold text-xl tracking-tight text-slate-900">
                SQL Analyst AI
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-500 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-200">
            <Database className="w-4 h-4" />
            <span className="hidden sm:inline">Active Context:</span>
            <span className="font-medium text-slate-700">
              {dbContext.connection.type}
            </span>
            <span className="text-slate-300">|</span>
            <span className="font-medium text-slate-700">
              {dbContext.connection.database}
            </span>
          </div>
        </header>

        {/* Chat Area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
          <div className="max-w-4xl mx-auto">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} dbContext={dbContext} />
            ))}
            {isLoading && (
              <div className="flex justify-start mb-8 animate-pulse">
                <div className="bg-white border border-slate-200 p-6 rounded-xl flex items-center gap-3">
                  <div
                    className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <div
                    className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <div
                    className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                  <span className="text-sm text-slate-500 font-medium">
                    Using {dbContext.selectedModel} to analyze...
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* Input Area */}
        <div className="bg-white border-t border-slate-200 p-4 shrink-0">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSubmit} className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  dbContext.schema
                    ? "Ask a question about your data..."
                    : "Please paste Schema Context in the sidebar first..."
                }
                className="w-full bg-slate-50 border border-slate-200 text-slate-900 rounded-xl py-4 pl-6 pr-14 text-base focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all shadow-sm placeholder:text-slate-400"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:hover:bg-indigo-600 transition-colors"
              >
                <Send size={20} />
              </button>
            </form>
            <div className="text-center mt-2 text-xs text-slate-400">
              AI can make mistakes. Please verify generated SQL queries before
              execution.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
