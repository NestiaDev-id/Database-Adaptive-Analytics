import type { DbContext } from "../types";

const API_BASE_URL = "http://localhost:8000";

/**
 * Generate SQL Analysis via Backend API
 * Menggunakan backend FastAPI yang akan memilih LLM provider
 * berdasarkan selectedModel di dbContext
 */
export const generateSqlAnalysis = async (
  query: string,
  dbContext: DbContext
): Promise<string> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: query,
        dbContext: dbContext,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "API request failed");
    }

    const data = await response.json();
    return data.content || "I could not generate a response. Please check your inputs.";
    
  } catch (error) {
    console.error("API Error:", error);
    return `Error connecting to backend API. Please ensure the server is running at ${API_BASE_URL}. Error: ${error}`;
  }
};

/**
 * Test database connection via backend
 */
export const testDatabaseConnection = async (
  connection: DbContext["connection"]
): Promise<{ success: boolean; message: string; tables?: string[] }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/connect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ connection }),
    });

    return await response.json();
  } catch (error) {
    return {
      success: false,
      message: `Connection error: ${error}`,
    };
  }
};

/**
 * Get database schema from backend
 */
export const getDatabaseSchema = async (
  connection: DbContext["connection"]
): Promise<{ success: boolean; schema_ddl?: string; error?: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/schema`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(connection),
    });

    return await response.json();
  } catch (error) {
    return {
      success: false,
      error: `Failed to get schema: ${error}`,
    };
  }
};

/**
 * Execute read-only SQL query via backend
 */
export const executeQuery = async (
  connection: DbContext["connection"],
  query: string
): Promise<{ success: boolean; columns?: string[]; rows?: any[]; error?: string }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/execute`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ connection, query }),
    });

    return await response.json();
  } catch (error) {
    return {
      success: false,
      error: `Query execution failed: ${error}`,
    };
  }
};

/**
 * List available AI models and their configuration status from backend
 */
export const getAvailableModels = async (): Promise<{ models: string[]; status: Record<string, boolean> }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/models`);
    const data = await response.json();
    return {
      models: data.models || [],
      status: data.status || {}
    };
  } catch (error) {
    console.error("Failed to fetch models:", error);
    return {
      models: ["Gemini (Google)", "GPT-4 (OpenAI)", "Groq (Llama 3)", "DeepSeek", "Mistral AI"],
      status: {}
    };
  }
};

/**
 * List supported database types and their configuration status from backend
 */
export const getSupportedDatabases = async (): Promise<{ supported: string[]; status: Record<string, boolean> }> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/databases`);
    const data = await response.json();
    return {
      supported: data.supported || [],
      status: data.status || {}
    };
  } catch (error) {
    console.error("Failed to fetch databases:", error);
    return {
      supported: ["PostgreSQL", "MySQL", "MongoDB"],
      status: {}
    };
  }
};
