import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type } from "@sinclair/typebox";
import { exec } from "child_process";
import { promisify } from "util";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

const execPromise = promisify(exec);

function readProviderKey(provider: string): string | undefined {
  const envMap: Record<string, string> = {
    openrouter: "OPENROUTER_API_KEY",
    groq: "GROQ_API_KEY",
  };
  const envKey = envMap[provider];
  if (envKey && process.env[envKey]) return process.env[envKey];

  try {
    const modelsPath = path.join(os.homedir(), ".pi", "agent", "models.json");
    if (fs.existsSync(modelsPath)) {
      const models = JSON.parse(fs.readFileSync(modelsPath, "utf8"));
      // or-free provider also holds OpenRouter key
      const key =
        models?.providers?.[provider]?.apiKey ??
        (provider === "openrouter" ? models?.providers?.["or-free"]?.apiKey : undefined);
      return key;
    }
  } catch {
    /* ignore */
  }
  return undefined;
}

interface AgentResult {
  agent: string;
  success: boolean;
  content: string;
  timeMs: number;
}

function escapeShellArg(arg: string): string {
  return arg.replace(/"/g, '\\"').replace(/`/g, "\\`").replace(/\$/g, "\\$");
}

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "parallel_agent_query",
    label: "Parallel Agent Query Orchestrator",
    description:
      "Queries cloud LLMs (OpenRouter, Groq) and CLI agents (OpenCode, Gemini CLI) in parallel or fallback. Local Ollama removed 2026-08-02.",
    parameters: Type.Object({
      prompt: Type.String({ description: "The prompt to send to the agents" }),
      mode: Type.Union([Type.Literal("parallel"), Type.Literal("fallback")], {
        description: "Execution mode: 'parallel' or 'fallback' (OpenRouter then Groq).",
        default: "parallel",
      }),
      agents: Type.Array(Type.String(), {
        description: "List of agents: 'openrouter', 'groq', 'opencode', 'gemini' (codex only if explicitly allowed).",
        default: ["openrouter", "groq", "opencode", "gemini"],
      }),
      openrouter_model: Type.Optional(
        Type.String({
          description: "OpenRouter model to use",
          default: "qwen/qwen3-coder:free",
        })
      ),
      groq_model: Type.Optional(
        Type.String({
          description: "Groq model to use (free tier, fast inference)",
          default: "llama-3.1-8b-instant",
        })
      ),
      gemini_model: Type.Optional(
        Type.String({
          description: "Gemini CLI model to use",
          default: "gemini-3-flash-preview",
        })
      ),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, _ctx) {
      const {
        prompt,
        mode,
        agents,
        openrouter_model = "qwen/qwen3-coder:free",
        gemini_model = "gemini-3-flash-preview",
        groq_model = "llama-3.1-8b-instant",
      } = params;
      const results: AgentResult[] = [];
      const startTime = Date.now();

      const queryOpenRouter = async (): Promise<AgentResult> => {
        const start = Date.now();
        try {
          const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${readProviderKey("openrouter") ?? ""}`,
            },
            body: JSON.stringify({
              model: openrouter_model,
              messages: [{ role: "user", content: prompt }],
            }),
            signal,
          });
          if (!res.ok) throw new Error(`OpenRouter returned status ${res.status}`);
          const data = (await res.json()) as any;
          return {
            agent: `OpenRouter (${openrouter_model})`,
            success: true,
            content: data.choices?.[0]?.message?.content || "Empty response",
            timeMs: Date.now() - start,
          };
        } catch (err: any) {
          return {
            agent: `OpenRouter (${openrouter_model})`,
            success: false,
            content: `Error: ${err.message}`,
            timeMs: Date.now() - start,
          };
        }
      };

      const queryCodex = async (): Promise<AgentResult> => {
        const start = Date.now();
        try {
          const escaped = escapeShellArg(prompt);
          const { stdout, stderr } = await execPromise(`codex exec "${escaped}"`, {
            cwd: process.cwd(),
          });
          return {
            agent: "Codex CLI",
            success: true,
            content: stdout || stderr || "No output",
            timeMs: Date.now() - start,
          };
        } catch (err: any) {
          return {
            agent: "Codex CLI",
            success: false,
            content: `Error: ${err.message}`,
            timeMs: Date.now() - start,
          };
        }
      };

      const queryOpenCode = async (): Promise<AgentResult> => {
        const start = Date.now();
        try {
          const escaped = escapeShellArg(prompt);
          const { stdout, stderr } = await execPromise(`opencode run "${escaped}"`, {
            cwd: process.cwd(),
          });
          return {
            agent: "OpenCode CLI",
            success: true,
            content: stdout || stderr || "No output",
            timeMs: Date.now() - start,
          };
        } catch (err: any) {
          return {
            agent: "OpenCode CLI",
            success: false,
            content: `Error: ${err.message}`,
            timeMs: Date.now() - start,
          };
        }
      };

      const queryGroq = async (): Promise<AgentResult> => {
        const start = Date.now();
        try {
          const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${readProviderKey("groq") ?? ""}`,
            },
            body: JSON.stringify({
              model: groq_model,
              messages: [{ role: "user", content: prompt }],
            }),
            signal,
          });
          if (!res.ok) throw new Error(`Groq returned status ${res.status}`);
          const data = (await res.json()) as any;
          return {
            agent: `Groq (${groq_model})`,
            success: true,
            content: data.choices?.[0]?.message?.content || "Empty response",
            timeMs: Date.now() - start,
          };
        } catch (err: any) {
          return {
            agent: `Groq (${groq_model})`,
            success: false,
            content: `Error: ${err.message}`,
            timeMs: Date.now() - start,
          };
        }
      };

      const queryGemini = async (): Promise<AgentResult> => {
        const start = Date.now();
        try {
          const escaped = escapeShellArg(prompt);
          const { stdout, stderr } = await execPromise(
            `gemini -m "${gemini_model}" -p "${escaped}"`,
            { cwd: process.cwd() }
          );
          return {
            agent: `Gemini CLI (${gemini_model})`,
            success: true,
            content: stdout || stderr || "No output",
            timeMs: Date.now() - start,
          };
        } catch (err: any) {
          return {
            agent: `Gemini CLI (${gemini_model})`,
            success: false,
            content: `Error: ${err.message}`,
            timeMs: Date.now() - start,
          };
        }
      };

      if (mode === "fallback") {
        const cloudRes = await queryOpenRouter();
        results.push(cloudRes);
        if (!cloudRes.success) {
          const groqRes = await queryGroq();
          results.push(groqRes);
          if (!groqRes.success) {
            results.push(await queryGemini());
          }
        }
      } else {
        const promises: Promise<AgentResult>[] = [];
        if (agents.includes("openrouter")) promises.push(queryOpenRouter());
        if (agents.includes("groq")) promises.push(queryGroq());
        if (agents.includes("codex")) promises.push(queryCodex());
        if (agents.includes("opencode")) promises.push(queryOpenCode());
        if (agents.includes("gemini")) promises.push(queryGemini());
        results.push(...(await Promise.all(promises)));
      }

      let markdownReport = `# 🧠 Parallel Orchestrator Results\n\n`;
      markdownReport += `**Prompt:** *${prompt}*\n`;
      markdownReport += `**Mode:** \`${mode}\` | **Total Execution Time:** \`${Date.now() - startTime}ms\`\n\n`;
      markdownReport += `| Agent | Status | Time | Response Summary |\n`;
      markdownReport += `| :--- | :--- | :--- | :--- |\n`;

      results.forEach((r) => {
        const status = r.success ? "🟢 Success" : "🔴 Failed";
        const cleanContent =
          r.content.substring(0, 120).replace(/\n/g, " ") + (r.content.length > 120 ? "..." : "");
        markdownReport += `| **${r.agent}** | ${status} | \`${r.timeMs}ms\` | ${cleanContent} |\n`;
      });

      markdownReport += `\n---\n\n## Detailed Responses\n\n`;
      results.forEach((r) => {
        markdownReport += `### 🤖 ${r.agent}\n`;
        markdownReport += `**Time:** \`${r.timeMs}ms\` | **Status:** ${r.success ? "🟢 Success" : "🔴 Failed"}\n\n`;
        markdownReport += `\`\`\`markdown\n${r.content}\n\`\`\`\n\n`;
      });

      return {
        content: [{ type: "text", text: markdownReport }],
        details: { results },
      };
    },
  });
}
