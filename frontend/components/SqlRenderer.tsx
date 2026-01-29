import React, { useMemo } from "react";
import { Check, Copy, Database } from "lucide-react";

interface SqlRendererProps {
  code: string;
  onCopy: (text: string) => void;
  copied: boolean;
  onRun?: (code: string) => void;
}

const SqlRenderer: React.FC<SqlRendererProps> = ({ code, onCopy, copied, onRun }) => {
  // 1. Analyze SQL Complexity
  const complexity = useMemo(() => {
    let score = 0;
    const upper = code.toUpperCase();
    if (upper.includes("JOIN")) score += 2;
    if (upper.includes("GROUP BY")) score += 1;
    if (upper.includes("HAVING")) score += 2;
    if (upper.includes("WITH")) score += 2; // CTE
    if (upper.includes("UNION")) score += 2;
    if (upper.includes("SELECT") && upper.includes("WHERE")) score += 1;
    
    if (score < 3) return { label: "Simple Query", color: "text-emerald-600 bg-emerald-50 border-emerald-200" };
    if (score < 6) return { label: "Intermediate Query", color: "text-blue-600 bg-blue-50 border-blue-200" };
    return { label: "Complex Analysis", color: "text-amber-600 bg-amber-50 border-amber-200" };
  }, [code]);

  // 2. Syntax Highlighting (Light Theme Colors)
  const highlightedHtml = useMemo(() => {
    let html = code
      // Prevent XSS injection from raw code before processing
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      // Comments (-- ...) -> Slate 500 italic
      .replace(/(--.*$)/gm, '<span class="text-slate-500 italic">$1</span>')
      // Strings ('...') -> Emerald 600
      .replace(/('.*?')/g, '<span class="text-emerald-600 border-b border-dotted border-emerald-200">$1</span>')
      // Numbers -> Amber 600
      .replace(/\b(\d+)\b/g, '<span class="text-amber-600 font-bold">$1</span>');

    // Keywords -> Fuchsia/Purple 600
    const keywords = [
      "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "OFFSET",
      "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "OUTER JOIN", "ON", "AS", "AND",
      "OR", "IN", "IS", "NULL", "NOT", "CASE", "WHEN", "THEN", "ELSE", "END", "WITH",
      "UNION", "ALL", "DISTINCT",
    ];
    // Functions -> Blue 600
    const functions = [
      "COUNT", "SUM", "AVG", "MIN", "MAX", "DATE_TRUNC", "TO_CHAR", "COALESCE", "NOW",
      "CURRENT_DATE", "ROUND", "CONCAT", "SUBSTRING", "CAST", "EXTRACT",
    ];

    keywords.forEach((kw) => {
      const regex = new RegExp(`\\b(${kw.replace(/ /g, "\\s+")})\\b`, "gi");
      html = html.replace(regex, (match) => {
        return `<span class="text-fuchsia-600 font-bold">${match}</span>`;
      });
    });

    functions.forEach((fn) => {
      const regex = new RegExp(`\\b(${fn})\\b`, "gi");
      html = html.replace(
        regex,
        `<span class="text-blue-600 font-semibold">$1</span>`,
      );
    });

    return html;
  }, [code]);

  return (
    <div className="my-6 rounded-lg overflow-hidden border border-slate-200 shadow-sm flex flex-col lg:flex-row bg-white">
      {/* Code Section */}
      <div className="flex-1 relative group/code">
        <div className="absolute right-2 top-2 z-10 opacity-0 group-hover/code:opacity-100 transition-opacity">
          <button
            onClick={() => onCopy(code)}
            className="p-1.5 bg-white backdrop-blur-sm rounded-md text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all border border-slate-200 shadow-sm"
            title="Copy SQL"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
        </div>
        <div className="text-xs text-slate-500 bg-slate-50 px-4 py-1.5 border-b border-slate-200 font-mono flex items-center gap-2 font-medium">
          <Database size={12} className="text-indigo-500" /> SQL QUERY
        </div>
        <pre className="p-4 overflow-x-auto text-sm font-mono leading-relaxed text-slate-700 custom-scrollbar bg-white">
          <code dangerouslySetInnerHTML={{ __html: highlightedHtml }} />
        </pre>
      </div>
      {/* Details Panel */}
      <div className="w-full lg:w-56 bg-slate-50 border-t lg:border-t-0 lg:border-l border-slate-200 p-4 text-slate-600 flex flex-col gap-4">
        <div>
          <div className="text-[10px] items-center gap-1 uppercase tracking-wider font-semibold text-slate-400 mb-2 flex">
             Complexity
          </div>
          <span className={`text-xs px-2 py-1 rounded-full border font-medium ${complexity.color}`}>
            {complexity.label}
          </span>
        </div>
        
        {onRun && (
          <button
            onClick={() => onRun(code)}
            className="flex items-center justify-center gap-2 w-full py-2 px-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm active:scale-95"
          >
            <div className="w-0 h-0 border-t-[5px] border-t-transparent border-l-[8px] border-l-white border-b-[5px] border-b-transparent ml-0.5" />
            Run Query
          </button>
        )}
      </div>
    </div>
  );
};

export default SqlRenderer;
