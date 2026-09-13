---
name: "🚨 Model Nerf / Regression Incident Report"
about: Report a suspected silent model degradation or behavioral shift
title: "[NERF REPORT] <Model Name> - <Short Summary>"
labels: ["incident", "nerf-detection"]
assignees: ""
---

### Model Affected
- **Model ID / Name:** (e.g., GPT-4o, Claude 3.5 Sonnet, DeepSeek V3)
- **Provider:** (e.g., OpenAI, Anthropic, Google, Groq)
- **Approximate Date / UTC Window:** 

### Observed Regression
Describe the specific capability that degraded (e.g. math accuracy, markdown formatting, instruction following, refusal spike):

### Reproduction Prompt
```text
[Paste exact user prompt here]
```

### Previous Output (Before Nerf)
```text
[Output when model was functioning well]
```

### Current Output (Degraded / Nerfed)
```text
[Current output showing degradation or failure]
```

### Telemetry Observations (Optional)
- Observed TTFT increase:
- Observed TPS collapse:
- Error message (if any):
