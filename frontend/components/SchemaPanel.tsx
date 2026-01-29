import React, { useState, useEffect } from "react";
import {
  Database,
  Table,
  Settings,
  Bot,
  Eye,
  EyeOff,
  Plug,
  ChevronDown,
  AlertTriangle,
} from "lucide-react";
import type { DbContext, AIModel } from "../types";
import { DatabaseTypes } from "../types";
import { testDatabaseConnection } from "../services/apiService";

interface SchemaPanelProps {
  dbContext: DbContext;
  setDbContext: React.Dispatch<React.SetStateAction<DbContext>>;
  isOpen: boolean;
}

const SchemaPanel: React.FC<SchemaPanelProps> = ({
  dbContext,
  setDbContext,
  isOpen,
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [schemaError, setSchemaError] = useState<string | null>(null);
  const [connectionMode, setConnectionMode] = useState<"local" | "cloud">(
    "local",
  );

  const [modelStatus, setModelStatus] = useState<Record<string, boolean>>({});
  const [dbStatus, setDbStatus] = useState<Record<string, boolean>>({});

  useEffect(() => {
    // Fetch available models and databases status
    const fetchData = async () => {
        const { status: mStatus } = await import("../services/apiService").then(m => m.getAvailableModels());
        setModelStatus(mStatus);
        
        // Initial Masking for Model
        setDbContext(prev => ({
            ...prev,
            apiKey: mStatus[prev.selectedModel] ? "********************" : prev.apiKey
        }));

        const { status: dStatus } = await import("../services/apiService").then(m => m.getSupportedDatabases());
        setDbStatus(dStatus);
        
        // Auto-detect cloud mode if configured in env for MongoDB
        if (dStatus["MongoDB"] && ["MongoDB", "CockroachDB"].includes(dbContext.connection.type)) {
             setConnectionMode("cloud");
             // Initial Masking for DB
             setDbContext(prev => ({
                ...prev,
                connection: {
                    ...prev.connection,
                    connection_string: "********************"
                }
             }));
        } else if (dStatus[dbContext.connection.type]) {
             // If current type is configured (e.g. Postgres local URI)
              setDbContext(prev => ({
                ...prev,
                connection: {
                    ...prev.connection,
                    connection_string: prev.connection.connection_string || "********************"
                }
             }));
        }
    };
    fetchData();

  }, []); // Run once on mount

  if (!isOpen) return null;

  const handleConnectionChange = (
    field: keyof typeof dbContext.connection,
    value: string | number,
  ) => {
    setDbContext((prev) => ({
      ...prev,
      connection: {
        ...prev.connection,
        [field]: value,
      },
    }));
  };

  const handleSchemaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setDbContext((prev) => ({ ...prev, schema: value }));
    validateSchema(value);
  };

  const validateSchema = (text: string) => {
    if (!text.trim()) {
      setSchemaError(null);
      return;
    }
    // Basic validation: check for common SQL DDL keywords
    const hasCreateTable = /CREATE\s+TABLE/i.test(text);
    const hasSelect = /SELECT/i.test(text); // Basic query check

    if (!hasCreateTable && !hasSelect) {
      setSchemaError(
        "Input doesn't look like valid SQL (missing 'CREATE TABLE').",
      );
    } else {
      setSchemaError(null);
    }
  };

  const [connectionStatus, setConnectionStatus] = useState<{
    status: "idle" | "success" | "error";
    message: string;
  }>({ status: "idle", message: "" });

  const handleConnect = async () => {
    setIsConnecting(true);
    setConnectionStatus({ status: "idle", message: "" });

    try {
      // Import dynamically to avoid circular dependency issues if any, 
      // or just ensure apiService is imported at top.
      // Assuming apiService is imported.
      const result = await testDatabaseConnection(dbContext.connection);

      if (result.success) {
        setConnectionStatus({
          status: "success",
          message: result.message || "Successfully connected to database.",
        });
        
        // Auto-fill schema if provided
        if (result.tables && result.tables.length > 0) {
            // Optional: Ask user or just notify they available
            // For now, let's just keep the status message clean
        }
      } else {
        setConnectionStatus({
          status: "error",
          message: result.message || "Failed to connect to database.",
        });
      }
    } catch (error: any) {
      setConnectionStatus({
        status: "error",
        message: error.message || "An unexpected error occurred.",
      });
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="w-80 border-r border-slate-200 bg-slate-50 flex flex-col h-full shrink-0 shadow-xl z-10 hidden md:flex font-sans">
      {/* Header */}
      <div className="p-5 border-b border-slate-200 flex items-center space-x-2 bg-white">
        <Settings className="w-5 h-5 text-slate-700" />
        <h2 className="font-bold text-slate-800 text-lg">Configuration</h2>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="p-5 space-y-8">
          {/* AI Model Section */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 text-slate-700 font-semibold">
              <Bot className="w-4 h-4" />
              <h3>AI Model</h3>
            </div>

            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-500">
                  Select Model
                </label>
                <div className="relative">
                  <select
                    value={dbContext.selectedModel}
                    onChange={(e) => {
                      const newModel = e.target.value as AIModel;
                      setDbContext((prev) => ({
                        ...prev,
                        selectedModel: newModel,
                        // Auto-fill mask if configured
                        apiKey: modelStatus[newModel] ? "********************" : "",
                      }));
                    }}
                    className="w-full appearance-none bg-white border border-slate-300 text-slate-700 py-2.5 px-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm"
                  >
                  <option value="Gemini (Google)">Gemini (Google)</option>
                    <option value="GPT-4 (OpenAI)">GPT-4 (OpenAI)</option>
                    <option value="Groq (Llama 3)">Groq (Llama 3)</option>
                    <option value="DeepSeek">DeepSeek</option>
                    <option value="Mistral AI">Mistral AI</option>
                  </select>
                  <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between">
                  <label className="text-xs font-medium text-slate-500">
                    API Key
                  </label>
                </div>
                <div className="relative">
                  <input
                    type={showApiKey ? "text" : "password"}
                    value={dbContext.apiKey || ""}
                    onChange={(e) =>
                      setDbContext((prev) => ({
                        ...prev,
                        apiKey: e.target.value,
                      }))
                    }
                    placeholder="Enter your API key here"
                    className="w-full bg-white border border-slate-300 text-slate-700 py-2.5 px-3 pr-10 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                  >
                    {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
            </div>
          </section>

          <hr className="border-slate-200" />

          {/* Database Connection Section */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 text-slate-700 font-semibold">
              <Database className="w-4 h-4" />
              <h3>Database Connection</h3>
            </div>

            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-medium text-slate-500">
                  Database Type
                </label>
                <div className="relative">
                  <select
                    value={dbContext.connection.type}
                    onChange={(e) => {
                      const newType = e.target.value;
                      handleConnectionChange("type", newType);
                      // Auto-fill mask if configured
                       if (dbStatus[newType] || (newType === "MongoDB" && dbStatus["MongoDB"])) {
                          handleConnectionChange("connection_string", "********************");
                       }
                    }}
                    className="w-full appearance-none bg-white border border-slate-300 text-slate-700 py-2.5 px-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm shadow-sm"
                  >
                    {DatabaseTypes.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-3 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>

              <div className="space-y-4">
                {/* Connection Mode Tabs */}
                <div className="flex p-1 bg-slate-100 rounded-lg">
                  <button
                    onClick={() => setConnectionMode("local")}
                    className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                      connectionMode === "local"
                        ? "bg-white text-slate-700 shadow-sm"
                        : "text-slate-500 hover:text-slate-600"
                    }`}
                  >
                    Local Connection
                  </button>
                  <button
                    onClick={() => setConnectionMode("cloud")}
                    className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                      connectionMode === "cloud"
                        ? "bg-white text-slate-700 shadow-sm"
                        : "text-slate-500 hover:text-slate-600"
                    }`}
                  >
                    Cloud / URI
                  </button>
                </div>

                {connectionMode === "local" ? (
                  <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
                    <div className="grid grid-cols-3 gap-3">
                      <div className="col-span-2 space-y-1">
                        <label className="text-xs font-medium text-slate-500">
                          Host
                        </label>
                        <input
                          type="text"
                          value={dbContext.connection.host}
                          onChange={(e) =>
                            handleConnectionChange("host", e.target.value)
                          }
                          className="w-full bg-white border border-slate-300 text-slate-700 py-2 px-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm shadow-sm"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs font-medium text-slate-500">
                          Port
                        </label>
                        <input
                          type="number"
                          value={dbContext.connection.port}
                          onChange={(e) =>
                            handleConnectionChange(
                              "port",
                              parseInt(e.target.value),
                            )
                          }
                          className="w-full bg-white border border-slate-300 text-slate-700 py-2 px-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm shadow-sm"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <label className="text-xs font-medium text-slate-500">
                          Username
                        </label>
                        <input
                          type="text"
                          value={dbContext.connection.username}
                          onChange={(e) =>
                            handleConnectionChange("username", e.target.value)
                          }
                          className="w-full bg-white border border-slate-300 text-slate-700 py-2 px-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm shadow-sm"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-xs font-medium text-slate-500">
                          Password
                        </label>
                        <div className="relative">
                          <input
                            type={showPassword ? "text" : "password"}
                            value={dbContext.connection.password}
                            onChange={(e) =>
                              handleConnectionChange("password", e.target.value)
                            }
                            className="w-full bg-white border border-slate-300 text-slate-700 py-2 px-3 pr-8 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm shadow-sm"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-2 top-2.5 text-slate-400 hover:text-slate-600"
                          >
                            {showPassword ? (
                              <EyeOff size={14} />
                            ) : (
                              <Eye size={14} />
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1 animate-in fade-in slide-in-from-top-2 duration-200">
                    <label className="text-xs font-medium text-slate-500">
                      Connection String (URI)
                    </label>
                    <input
                      type="text"
                      value={dbContext.connection.connection_string || ""}
                      onChange={(e) =>
                        handleConnectionChange(
                          "connection_string",
                          e.target.value,
                        )
                      }
                      placeholder={
                        dbContext.connection.type === "MongoDB"
                          ? "mongodb+srv://user:pass@cluster..."
                          : "postgresql://user:pass@localhost:5432/db"
                      }
                      className="w-full bg-white border border-slate-300 text-slate-700 py-2 px-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm shadow-sm"
                    />
                    <p className="text-[10px] text-slate-500 italic">
                      Gunakan ini untuk koneksi Cloud (Atlas, Neon, Supabase,
                      dll).
                    </p>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                {/* Connection Status Notification */}
                {connectionStatus.status !== "idle" && (
                  <div
                    className={`p-3 rounded-lg text-xs flex items-start gap-2 ${
                      connectionStatus.status === "success"
                        ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        : "bg-red-50 text-red-700 border border-red-200"
                    }`}
                  >
                    {connectionStatus.status === "success" ? (
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    ) : (
                      <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" />
                    )}
                    <div className="flex-1">
                      <p className="font-semibold mb-0.5">
                        {connectionStatus.status === "success"
                          ? "Connected Successfully"
                          : "Connection Failed"}
                      </p>
                      <p className="opacity-90 leading-relaxed">
                        {connectionStatus.message}
                      </p>
                    </div>
                  </div>
                )}

                <button
                  onClick={handleConnect}
                  disabled={isConnecting}
                  className={`w-full mt-2 font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-sm ${
                    connectionStatus.status === "success"
                      ? "bg-emerald-600 hover:bg-emerald-700 text-white"
                      : "bg-red-500 hover:bg-red-600 text-white"
                  }`}
                >
                  {isConnecting ? (
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : connectionStatus.status === "success" ? (
                    <Plug className="w-4 h-4" />
                  ) : (
                    <Plug className="w-4 h-4" />
                  )}
                  {isConnecting ? "Connecting..." : "Connect to Database"}
                </button>
              </div>
            </div>
          </section>

          <hr className="border-slate-200" />

          {/* Schema Context (Required for AI) */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-semibold text-slate-600 flex items-center gap-2">
                <Table className="w-3 h-3" />
                Schema Context
              </label>
              <span className="text-[10px] text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full font-medium">
                Required
              </span>
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">
              Since this is a client-side AI analysis tool, please paste your
              table definitions (DDL) below so the model understands your
              structure.
            </p>
            <div className="relative">
              <textarea
                value={dbContext.schema}
                onChange={handleSchemaChange}
                placeholder={`Example:
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  price DECIMAL(10,2),
  stock INT DEFAULT 0
);

CREATE TABLE sales (
  id SERIAL PRIMARY KEY,
  product_id INT REFERENCES products(id),
  quantity INT,
  sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);`}
                className={`w-full h-64 p-4 text-xs font-mono bg-white text-slate-700 rounded-lg border focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none leading-relaxed shadow-sm transition-all ${
                  schemaError
                    ? "border-amber-500 focus:ring-amber-500"
                    : "border-slate-300"
                }`}
                spellCheck={false}
              />
              {schemaError && (
                <div className="mt-1 flex items-start gap-1.5 text-amber-600 text-[10px] leading-tight font-medium">
                  <AlertTriangle className="w-3 h-3 shrink-0 mt-0.5" />
                  <span>{schemaError}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SchemaPanel;
