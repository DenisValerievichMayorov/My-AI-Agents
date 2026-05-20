# 🫵 Реестр жалоб ИИ-Агентов (GMC Complaints Registry)

Этот файл содержит автоматические жалобы фоновых агентов на ошибки и сбои, требующие оперативного вмешательства и исправления со стороны Antigravity.


## 🔴 [DESKTOP-85D3NJI] - 2026-05-17 17:31:36
- **Действие:** `Gemini CLI execution`
- **Ошибка:**
  ```text
  Warning: 256-color support not detected. Using a terminal with at least 256-color support is recommended for a better visual experience.
YOLO mode is enabled. All tool calls will be automatically approved.
YOLO mode is enabled. All tool calls will be automatically approved.
Ripgrep is not available. Falling back to GrepTool.
Skill conflict detected: "whatsapp-bridge-manager" from "C:\Users\anton\.agents\skills\whatsapp-bridge-manager\SKILL.md" is overriding the same skill from "C:\Users\anton\.gemini\skills\whatsapp-bridge-manager\SKILL.md".
Skill conflict detected: "system-maintenance" from "C:\Users\anton\.agents\skills\system-maintenance\SKILL.md" is overriding the same skill from "C:\Users\anton\.gemini\skills\system-maintenance\SKILL.md".
Skill conflict detected: "report-generator-expert" from "C:\Users\anton\.agents\skills\report-generator-expert\SKILL.md" is overriding the same skill from "C:\Users\anton\.gemini\skills\report-generator-expert\SKILL.md".
Skill conflict detected: "gps-logger-master" from "C:\Users\anton\.agents\skills\gps-logger-master\SKILL.md" is overriding the same skill from "C:\Users\anton\.gemini\skills\gps-logger-master\SKILL.md".
Skill conflict detected: "git-flow-manager" from "C:\Users\anton\.agents\skills\git-flow-manager\SKILL.md" is overriding the same skill from "C:\Users\anton\.gemini\skills\git-flow-manager\SKILL.md".
Skill conflict detected: "email-summarizer-pro" from "C:\Users\anton\.agents\skills\email-summarizer-pro\SKILL.md" is overriding the same skill from "C:\Users\anton\.gemini\skills\email-summarizer-pro\SKILL.md".
Error generating content via API. Full report available at: C:\Users\anton\AppData\Local\Temp\gemini-client-error-generateJson-api-2026-05-17T15-31-35-540Z.json TerminalQuotaError: You have exhausted your capacity on this model. Your quota will reset after 16h0m43s.
    at classifyGoogleError (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270063:18)
    at retryWithBackoff (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270707:31)
    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)
    at async BaseLlmClient._generateWithRetry (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270941:14)
    at async BaseLlmClient.generateJson (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270848:21)
    at async NumericalClassifierStrategy.route (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318678:28)
    at async CompositeStrategy.route (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318743:26)
    at async ModelRouterService.route (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318904:18)
    at async GeminiClient.processTurn (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306691:24)
    at async GeminiClient.sendMessageStream (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306797:14) {
  cause: {
    code: 429,
    message: 'You have exhausted your capacity on this model. Your quota will reset after 16h0m43s.',
    details: [ [Object], [Object] ]
  },
  retryDelayMs: 57643562.854457,
  reason: 'QUOTA_EXHAUSTED'
}
[Routing] NumericalClassifierStrategy failed: Error: Failed to generate content: You have exhausted your capacity on this model. Your quota will reset after 16h0m43s.
    at BaseLlmClient._generateWithRetry (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270971:13)
    at async BaseLlmClient.generateJson (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270848:21)
    at async NumericalClassifierStrategy.route (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318678:28)
    at async CompositeStrategy.route (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318743:26)
    at async ModelRouterService.route (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:318904:18)
    at async GeminiClient.processTurn (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306691:24)
    at async GeminiClient.sendMessageStream (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306797:14)
    at async file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/gemini-QSTQ2DBG.js:10859:26
    at async main (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/gemini-QSTQ2DBG.js:16137:5)
Error when talking to Gemini API Full report available at: C:\Users\anton\AppData\Local\Temp\gemini-client-error-Turn.run-sendMessageStream-2026-05-17T15-31-36-057Z.json TerminalQuotaError: You have exhausted your capacity on this model. Your quota will reset after 21h29m22s.
    at classifyGoogleError (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270063:18)
    at retryWithBackoff (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:270707:31)
    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)
    at async GeminiChat.makeApiCallAndProcessStream (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:293631:28)
    at async GeminiChat.streamWithRetries (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:293450:29)
    at async Turn.run (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:294024:24)
    at async GeminiClient.processTurn (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306709:22)
    at async GeminiClient.sendMessageStream (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/chunk-7VVHSNDQ.js:306797:14)
    at async file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/gemini-QSTQ2DBG.js:10859:26
    at async main (file:///C:/Users/anton/AppData/Roaming/npm/node_modules/@google/gemini-cli/bundle/gemini-QSTQ2DBG.js:16137:5) {
  cause: {
    code: 429,
    message: 'You have exhausted your capacity on this model. Your quota will reset after 21h29m22s.',
    details: [ [Object], [Object] ]
  },
  retryDelayMs: 77362038.66728301,
  reason: 'QUOTA_EXHAUSTED'
}
An unexpected critical error occurred:[object Object]
  ```
- **Статус:** ⏳ Ожидает рассмотрения и исправления от Antigravity.
---
