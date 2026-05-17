# 🫵 Реестр жалоб ИИ-Агентов (GMC Complaints Registry)

Этот файл содержит автоматические жалобы фоновых агентов на ошибки и сбои, требующие оперативного вмешательства и исправления со стороны Antigravity.


## 🔴 [penguin] - 2026-05-17 10:20:52
- **Действие:** `Gemini CLI execution`
- **Ошибка:**
  ```text
  Warning: 256-color support not detected. Using a terminal with at least 256-color support is recommended for a better visual experience.
YOLO mode is enabled. All tool calls will be automatically approved.
YOLO mode is enabled. All tool calls will be automatically approved.
Ripgrep is not available. Falling back to GrepTool.
Skill conflict detected: "powerpoint" from "/home/denisvalerievichmayorov1/Sync/.gemini/skills/powerpoint/SKILL.md" is overriding the same skill from "/home/denisvalerievichmayorov1/.gemini/skills/powerpoint/SKILL.md".
Skill conflict detected: "ocr-and-documents" from "/home/denisvalerievichmayorov1/Sync/.gemini/skills/ocr-and-documents/SKILL.md" is overriding the same skill from "/home/denisvalerievichmayorov1/.gemini/skills/ocr-and-documents/SKILL.md".
Skill conflict detected: "himalaya" from "/home/denisvalerievichmayorov1/Sync/.gemini/skills/himalaya/SKILL.md" is overriding the same skill from "/home/denisvalerievichmayorov1/.gemini/skills/himalaya/SKILL.md".
Skill conflict detected: "google-workspace" from "/home/denisvalerievichmayorov1/Sync/.gemini/skills/google-workspace/SKILL.md" is overriding the same skill from "/home/denisvalerievichmayorov1/.gemini/skills/google-workspace/SKILL.md".
API returned invalid content after all retries. Full report available at: /tmp/gemini-client-error-generateJson-invalid-content-2026-05-17T08-20-52-337Z.json Error: Retry attempts exhausted
    at retryWithBackoff (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270798:9)
    at async BaseLlmClient._generateWithRetry (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270941:14)
    at async BaseLlmClient.generateJson (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270848:21)
    at async NumericalClassifierStrategy.route (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318678:28)
    at async CompositeStrategy.route (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318743:26)
    at async ModelRouterService.route (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318904:18)
    at async GeminiClient.processTurn (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306691:24)
    at async GeminiClient.sendMessageStream (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306797:14)
    at async file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/gemini-QSTQ2DBG.js:10859:26
    at async main (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/gemini-QSTQ2DBG.js:16137:5)
[Routing] NumericalClassifierStrategy failed: Error: Failed to generate content: Retry attempts exhausted
    at BaseLlmClient._generateWithRetry (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270971:13)
    at async BaseLlmClient.generateJson (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270848:21)
    at async NumericalClassifierStrategy.route (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318678:28)
    at async CompositeStrategy.route (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318743:26)
    at async ModelRouterService.route (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318904:18)
    at async GeminiClient.processTurn (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306691:24)
    at async GeminiClient.sendMessageStream (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306797:14)
    at async file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/gemini-QSTQ2DBG.js:10859:26
    at async main (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/gemini-QSTQ2DBG.js:16137:5)
Error when talking to Gemini API Full report available at: /tmp/gemini-client-error-Turn.run-sendMessageStream-2026-05-17T08-20-52-781Z.json TerminalQuotaError: You have exhausted your capacity on this model. Your quota will reset after 4h39m43s.
    at classifyGoogleError (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270063:18)
    at retryWithBackoff (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270707:31)
    at process.processTicksAndRejections (node:internal/process/task_queues:103:5)
    at async GeminiChat.makeApiCallAndProcessStream (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:293631:28)
    at async GeminiChat.streamWithRetries (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:293450:29)
    at async Turn.run (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:294024:24)
    at async GeminiClient.processTurn (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306709:22)
    at async GeminiClient.sendMessageStream (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306797:14)
    at async file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/gemini-QSTQ2DBG.js:10859:26
    at async main (file:///home/denisvalerievichmayorov1/.npm-global/lib/node_modules/@google/gemini-cli/bundle/gemini-QSTQ2DBG.js:16137:5) {
  cause: {
    code: 429,
    message: 'You have exhausted your capacity on this model. Your quota will reset after 4h39m43s.',
    details: [ [Object], [Object] ]
  },
  retryDelayMs: 16783922.348283,
  reason: 'QUOTA_EXHAUSTED'
}
An unexpected critical error occurred:[object Object]
  ```
- **Статус:** ⏳ Ожидает рассмотрения и исправления от Antigravity.
---
