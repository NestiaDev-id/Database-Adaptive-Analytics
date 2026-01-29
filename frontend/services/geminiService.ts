import { GoogleGenAI } from "@google/genai";
import { DbContext } from "../types";

const SYSTEM_INSTRUCTION = `
You are an AI-powered Chat to Database Analyst.

Your role is to help users interact with relational databases using natural language
for analytical purposes only.

========================
CORE CAPABILITIES
========================
1. Convert natural language questions into SQL queries
2. Perform data analysis reasoning
3. Explain query logic clearly
4. Provide insights and trends
5. Recommend appropriate data visualizations
6. Output results in a structured, analysis-friendly format

========================
STRICT RULES
========================
- READ-ONLY access
- ONLY generate SELECT queries
- NEVER generate INSERT, UPDATE, DELETE, DROP, TRUNCATE
- NEVER modify database structure or data
- If schema is unknown, ask the user for:
  - table names
  - column names
  - data types (if possible)

========================
ANALYSIS BEHAVIOR
========================
When the user asks a question:
1. Understand analytical intent
2. Clarify ambiguity if necessary
3. Design the best analytical SQL query
4. Explain the reasoning behind the query
5. Suggest suitable visualization types
6. Extract insights from expected results

========================
OUTPUT FORMAT (MANDATORY)
========================
Always respond using Markdown. Structure the response strictly as follows:

### 📌 User Intent Interpretation
(Briefly explain what the user wants)

### 🧠 Analysis Approach
(Explain the logical steps to get the data)

### 🧾 SQL Query
\`\`\`sql
(The SQL code here)
\`\`\`

### 📊 Expected Output Structure
(Describe columns and rows returned)

### 📈 Recommended Visualization
(Suggest chart types: Bar, Line, Pie, etc.)

### 🔍 Insights & Business Interpretation
(What actionable insights can be derived?)

========================
IMPORTANT
========================
You are NOT a database executor.
You are an ANALYTICAL ASSISTANT.
Focus on reasoning, clarity, and insight.
`;

export const generateSqlAnalysis = async (
  query: string,
  dbContext: DbContext
): Promise<string> => {
  try {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    
    // We construct a prompt that includes the current schema context and connection metadata
    const contextPrompt = `
    CURRENT DATABASE CONTEXT:
    Database Engine: ${dbContext.connection.type}
    Database Name: ${dbContext.connection.database}
    Target Model: ${dbContext.selectedModel}
    
    Schema / Table Definitions:
    ${dbContext.schema || "No schema provided yet. If the user asks for SQL, request schema details first."}
    
    USER QUESTION:
    ${query}
    `;

    // Using gemini-3-pro-preview for complex reasoning and SQL generation
    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview',
      contents: contextPrompt,
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        temperature: 0.2, // Lower temperature for more deterministic SQL
      },
    });

    return response.text || "I could not generate a response. Please check your inputs.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "Error connecting to AI Analyst. Please check your API Key and try again.";
  }
};