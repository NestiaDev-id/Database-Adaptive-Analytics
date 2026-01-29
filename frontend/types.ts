export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export type AIModel = 'Gemini (Google)' | 'GPT-4 (OpenAI)' | 'Groq (Llama 3)' | 'DeepSeek' | 'Mistral AI';

export interface DbConnection {
  host: string;
  port: number;
  username: string;
  password: string;
  database: string;
  type: DatabaseType;
  connection_string?: string;
}

export interface DbContext {
  connection: DbConnection;
  schema: string;
  selectedModel: AIModel;
  apiKey?: string;
}

export type DatabaseType = 'PostgreSQL' | 'MySQL' | 'SQL Server' | 'SQLite' | 'Oracle' | 'Snowflake' | 'BigQuery' | 'MongoDB';

export const DatabaseTypes: DatabaseType[] = [
  'PostgreSQL',
  'MySQL',
  'SQL Server',
  'SQLite',
  'Oracle',
  'Snowflake',
  'BigQuery',
  'MongoDB'
];