import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Bot,
  User,
  Copy,
  Check,
  Quote,
  AlertTriangle,

  Activity,

} from "lucide-react";
import { executeQuery } from "../services/apiService";
import type { DbContext, Message } from "../types";
import mermaid from "mermaid";
import DataVisualizer from "./DataVisualizer";
import SqlRenderer from "./SqlRenderer";

// Define props interface locally since it was missing
interface ChatMessageProps {
  message: Message;
  dbContext?: DbContext;
}

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'inherit',
});

// Mermaid Renderer Component
const MermaidRenderer: React.FC<{ code: string }> = ({ code }) => {
  const [svg, setSvg] = React.useState<string>("");
  const [error, setError] = React.useState<string | null>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    let isMounted = true;
    
    const renderDiagram = async () => {
      try {
        if (!code) return;
        // Unique ID for each diagram
        const id = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(id, code);
        
        if (isMounted) {
          setSvg(svg);
          setError(null);
        }
      } catch (err) {
        console.error("Mermaid error:", err);
        if (isMounted) {
          setError("Failed to render diagram. Syntax error?");
        }
      }
    };

    renderDiagram();

    return () => {
      isMounted = false;
    };
  }, [code]);

  if (error) {
    return (
      <div className="bg-red-50 text-red-600 p-4 rounded-lg my-4 text-sm font-mono border border-red-200">
        <div className="flex items-center gap-2 mb-2 font-bold">
          <AlertTriangle size={16} /> Diagram Error
        </div>
        {error}
        <pre className="mt-2 text-xs text-red-400 opacity-70 overflow-x-auto">
          {code}
        </pre>
      </div>
    );
  }

  return (
    <div className="my-6 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
      <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex items-center gap-2 text-xs font-medium text-slate-500 uppercase tracking-wider">
        <Activity size={12} className="text-indigo-500" /> Diagram
      </div>
      <div 
        ref={containerRef}
        className="p-6 overflow-x-auto flex justify-center bg-white"
        dangerouslySetInnerHTML={{ __html: svg }} 
      />
    </div>
  );
};

const ChatMessage: React.FC<ChatMessageProps> = ({ message, dbContext }) => {
  const isUser = message.role === "user";
  const [copied, setCopied] = React.useState(false);

  // Query Execution State
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<{
    headers: string[];
    data: any[];
    error?: string;
  } | null>(null);
  
  // Ref to track if we've already auto-run the query for this message
  // strictly to prevent double-execution in React Strict Mode or on re-renders
  const hasAutoRun = React.useRef(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunQuery = async (sql: string) => {
      if (!dbContext) return;
      
      setIsExecuting(true);
      setExecutionResult(null);
      
      try {
          const result = await executeQuery(dbContext.connection, sql);
          
          if (result.success && result.columns && result.rows) {
             setExecutionResult({
                 headers: result.columns,
                 data: result.rows
             });
          } else {
             setExecutionResult({
                 headers: [],
                 data: [],
                 error: result.error || "Unknown error occurred"
             });
          }
      } catch (err) {
          setExecutionResult({
                 headers: [],
                 data: [],
                 error: String(err)
             });
      } finally {
          setIsExecuting(false);
      }
  };

  // Auto-Run Effect
  React.useEffect(() => {
    if (!dbContext || hasAutoRun.current || message.role !== 'assistant') return;

    // Regex to find the first SQL block
    const sqlMatch = message.content.match(/```sql\n([\s\S]*?)\n```/);
    if (sqlMatch && sqlMatch[1]) {
      const sql = sqlMatch[1].trim();
      // Only auto-run SELECT statements for safety
      if (sql.toUpperCase().startsWith('SELECT') || sql.toUpperCase().startsWith('WITH')) {
        hasAutoRun.current = true;
        handleRunQuery(sql);
      }
    }
  }, [message.content, dbContext, message.role]);

  // Helper to extract table data from HAST node
  const extractTableData = (node: any) => {
    try {
      // Helper to safely get text content from any HAST node recursively
      const getText = (n: any): string => {
        if (!n) return "";
        if (n.type === "text") return n.value || "";
        if (n.children && Array.isArray(n.children)) {
          return n.children.map(getText).join("");
        }
        return "";
      };

      // HAST structure: table -> thead/tbody -> tr -> th/td
      const children = node.children || [];

      // Find thead and tbody (ignoring text nodes like whitespace)
      const thead = children.find((c: any) => c.tagName === "thead");
      const tbody = children.find((c: any) => c.tagName === "tbody");

      // Without a header, we can't label the chart axes reliably
      if (!thead) return null;

      // Extract headers from the first row of thead
      const headerRow = thead.children?.find((c: any) => c.tagName === "tr");
      if (!headerRow) return null;

      const headers = headerRow.children
        .filter((c: any) => c.tagName === "th")
        .map((th: any) => getText(th).trim());

      if (headers.length === 0) return null;

      // Extract data rows from tbody
      const dataRows = tbody
        ? tbody.children.filter((c: any) => c.tagName === "tr")
        : [];

      const data = dataRows.map((row: any) => {
        const rowData: Record<string, any> = {};
        const cells = row.children.filter((c: any) => c.tagName === "td");

        cells.forEach((cell: any, index: number) => {
          if (index < headers.length) {
            const header = headers[index];
            const textValue = getText(cell).trim();

            let value: string | number = textValue;

            // Simple number parsing
            // Remove commas only if they look like thousands separators
            const cleanNum = textValue.replace(/,/g, "");
            const num = parseFloat(cleanNum);

            // Check if strictly numeric (allowing decimals and negative)
            // This avoids converting dates like "2023-01" to 2023
            if (!isNaN(num) && isFinite(num)) {
              // Check against regex to ensure it's not a date or mixed string
              // Matches: 123, -123, 123.45, 1,234.56
              // Does not match: 2023-01, 123abc
              if (/^-?[\d,]+(\.\d+)?$/.test(textValue)) {
                value = num;
              }
            }

            rowData[header] = value;
          }
        });
        return rowData;
      });

      if (data.length === 0) return null;

      return { headers, data };
    } catch (e) {
      console.error("Error extracting table data", e);
      return null;
    }
  };

  return (
    <div
      className={`flex w-full ${isUser ? "justify-end" : "justify-start"} mb-8 group`}
    >
      <div
        className={`flex max-w-4xl w-full gap-4 ${isUser ? "flex-row-reverse" : "flex-row"}`}
      >
        {/* Avatar */}
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
            isUser ? "bg-indigo-600 text-white" : "bg-emerald-600 text-white"
          }`}
        >
          {isUser ? <User size={20} /> : <Bot size={20} />}
        </div>

        {/* Content */}
        <div className={`flex-1 overflow-hidden min-w-0`}>
          <div
            className={`flex items-baseline gap-2 mb-1 ${isUser ? "justify-end" : "justify-start"}`}
          >
            <span className="font-semibold text-sm text-slate-700">
              {isUser ? "You" : "SQL Analyst AI"}
            </span>
            <span className="text-xs text-slate-400">
              {message.timestamp.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
          </div>

          <div
            className={`rounded-xl p-6 shadow-sm border ${
              isUser
                ? "bg-indigo-50 border-indigo-100 text-slate-800"
                : "bg-white border-slate-200 text-slate-800"
            }`}
          >
            <div className="prose prose-slate max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Custom Renderers for Styled Markdown
                  h1: ({ children }) => (
                    <h1 className="text-2xl font-bold text-slate-900 mt-6 mb-4 pb-2 border-b border-slate-200 first:mt-0">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-xl font-bold text-slate-800 mt-6 mb-3 pb-2 border-b border-slate-200">
                      {children}
                    </h2>
                  ),
                  // H3 is used for main sections in our AI prompt. We add a top border to create a separator line.
                  h3: ({ children }) => (
                    <h3 className="text-lg font-bold text-indigo-700 mt-8 mb-3 pt-4 border-t border-slate-200 flex items-center gap-2">
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p className="mb-4 leading-relaxed text-slate-700 text-[15px]">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc list-outside ml-6 mb-4 space-y-1.5 text-slate-700 marker:text-indigo-400">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal list-outside ml-6 mb-4 space-y-1.5 text-slate-700 marker:text-indigo-600 font-medium">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => <li className="pl-1">{children}</li>,
                  strong: ({ children }) => (
                    <strong className="font-semibold text-slate-900 bg-slate-100 px-1 py-0.5 rounded border border-slate-200/50">
                      {children}
                    </strong>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-indigo-400 pl-4 py-1 my-4 bg-slate-50 text-slate-600 italic rounded-r-lg">
                      <div className="flex gap-2">
                        <Quote
                          size={16}
                          className="text-indigo-300 shrink-0 mt-1"
                        />
                        <div>{children}</div>
                      </div>
                    </blockquote>
                  ),
                  hr: () => <hr className="my-8 border-slate-200 border-t-2" />,
                  // Code block renderer
                  code({ className, children }) {
                    const match = /language-(\w+)/.exec(className || "");
                    
                    // Safely handle children if not string
                    let codeText = "";
                    if (Array.isArray(children)) {
                      codeText = children.map((c) => String(c)).join("");
                    } else {
                      codeText = String(children);
                    }
                    codeText = codeText.replace(/\n$/, "");
                    
                    const isSql = match && match[1].toLowerCase() === "sql";
                    const isMongodb = match && match[1].toLowerCase() === "mongodb";
                    const isMermaid = match && match[1].toLowerCase() === "mermaid";

                    if (isMermaid) {
                      return <MermaidRenderer code={codeText} />;
                    }

                    if (isSql || isMongodb) {
                      return (
                        <div className="flex flex-col gap-4">
                            <SqlRenderer
                              code={codeText}
                              onCopy={handleCopy}
                              copied={copied}
                              onRun={dbContext ? handleRunQuery : undefined}

                            />
                            
                            {/* Execution Result Area */}
                            {isExecuting && (
                                <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg flex items-center gap-3 animate-pulse">
                                    <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                                    <span className="text-sm text-slate-600">Executing query on database...</span>
                                </div>
                            )}
                            
                            {executionResult && executionResult.error && (
                                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                                    <div className="font-bold mb-1 flex items-center gap-2">
                                        <AlertTriangle size={16} /> Execution Failed
                                    </div>
                                    <div className="font-mono text-xs opacity-90">{executionResult.error}</div>
                                </div>
                            )}
                            
                            {executionResult && !executionResult.error && executionResult.data && (
                                <div className="mt-2">
                                    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                                        <Activity size={12} className="text-emerald-500" /> Query Results
                                    </div>
                                    <DataVisualizer 
                                        headers={executionResult.headers} 
                                        data={executionResult.data} 
                                    />
                                </div>
                            )}
                        </div>
                      );
                    }

                    return match ? (
                      <div className="relative group/code my-6 rounded-lg overflow-hidden shadow-sm border border-slate-800">
                        <div className="absolute right-0 top-0 p-2 flex justify-end opacity-0 group-hover/code:opacity-100 transition-opacity z-10">
                          <button
                            onClick={() => handleCopy(codeText)}
                            className="p-1.5 bg-slate-700/80 backdrop-blur-sm rounded-md text-slate-300 hover:text-white hover:bg-slate-600 transition-all border border-slate-600"
                            title="Copy code"
                          >
                            {copied ? <Check size={14} /> : <Copy size={14} />}
                          </button>
                        </div>
                        <div className="bg-slate-900 text-slate-400 text-xs px-4 py-1.5 border-b border-slate-800 font-mono uppercase tracking-wider flex items-center gap-2">
                          {match[1]}
                        </div>
                        <pre
                          className={`${className} p-4 bg-[#0d1117] overflow-x-auto m-0`}
                        >
                          <code className={className}>
                            {children}
                          </code>
                        </pre>
                      </div>
                    ) : (
                      <code
                        className={`${className} bg-slate-100 px-1.5 py-0.5 rounded text-sm font-mono text-slate-800 border border-slate-200`}
                      >
                        {children}
                      </code>
                    );
                  },
                  // Custom Table Renderer
                  table({ node }) {
                    let tableInfo = null;
                    try {
                      tableInfo = extractTableData(node);
                    } catch (e) {
                      console.error("Failed to extract table", e);
                    }

                    if (tableInfo) {
                      return (
                        <DataVisualizer
                          data={tableInfo.data}
                          headers={tableInfo.headers}
                        />
                      );
                    }

                    // User-friendly fallback if extraction fails
                    return (
                      <div className="my-4 p-4 bg-slate-50 border border-slate-200 rounded-lg flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                        <div className="space-y-1">
                          <p className="text-sm font-medium text-slate-700">
                            Visualizer Unavailable
                          </p>
                          <p className="text-xs text-slate-500 leading-relaxed">
                            The table data could not be parsed for the
                            interactive view. This usually happens with complex
                            table structures or missing headers.
                          </p>
                        </div>
                      </div>
                    );
                  },
                  // Suppress default table elements since we handle 'table'
                  thead: () => null,
                  tbody: () => null,
                  tr: () => null,
                  th: () => null,
                  td: () => null,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
