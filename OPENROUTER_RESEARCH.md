# OpenRouter Research

## What is OpenRouter?

OpenRouter (openrouter.ai) is a **unified API gateway and marketplace** for large language models. It acts as an abstraction layer between your application and dozens of AI providers, giving you access to **500+ models from 60+ providers** through a single API endpoint and a single API key.

Founded by **Alex Atallah** (co-founder of OpenSea), OpenRouter has raised a **Series A from Sequoia, Andreessen Horowitz, and Menlo Ventures**.

- **250k+ apps** use OpenRouter
- **4.2M+ users** globally
- Handles **billions of requests** and **trillions of tokens** weekly

---

## How It Works

```
Your App → OpenRouter API → AI Provider (OpenAI, Anthropic, Google, etc.) → OpenRouter → Your App
```

1. Your application sends a request to `https://openrouter.ai/api/v1/chat/completions`
2. OpenRouter translates your request into the provider's native API format
3. The provider processes the request and returns a response
4. OpenRouter normalizes the response and returns it in a unified format

The API is **fully OpenAI-compatible** — most integrations require changing only the base URL and API key. You can use the official OpenAI SDK directly.

---

## Key Features

### 1. Unified, OpenAI-Compatible API
- Single endpoint for all models
- Compatible with the OpenAI SDK (Python and TypeScript/JS)
- Normalized response schema across all models and providers
- Supports streaming via Server-Sent Events (SSE)
- New Responses API (Beta) — drop-in replacement for OpenAI's Responses API

### 2. Intelligent Routing & Fallbacks
- Automatic provider selection based on cost, latency, and availability
- Automatic failover if a provider is down or rate-limited
- Model variants:
  - `:free` — Always free, with low rate limits
  - `:extended` — Longer-than-usual context length
  - `:nitro` — Optimized for speed
  - `:floor` — Most cost-effective
  - `:exacto` — Only OpenRouter-curated high-quality endpoints

### 3. BYOK (Bring Your Own Key)
- Configure your own provider API keys (e.g., your own OpenAI key)
- OpenRouter prioritizes routing to your own endpoints
- 5% fee on upstream usage when using your own keys

### 4. Multimodal Support
- Text, images, PDFs, and document inputs
- Tool calling / function calling
- Web search integration
- Reasoning capabilities

### 5. Centralized Billing
- Single credit balance across all providers
- Pay-as-you-go with per-token billing
- No monthly fees or minimum commitments
- Auto-replenishment available

### 6. Privacy & Security
- Zero-logging by default (prompts and completions are not logged)
- Only metadata logged (timestamps, model used, token counts)
- Opt-in logging for a 1% usage discount
- Provider routing respects privacy settings
- GDPR compliance and EU region locking available

### 7. Enterprise Features
- Custom data policies
- Observability integrations (Langfuse, Datadog, Braintrust)
- Token usage, cost, and latency monitoring
- Volume-based pricing with annual commits
- Regional routing

---

## Supported Models & Providers

### Providers
OpenRouter aggregates models from all major providers including:
- **Anthropic** (Claude family)
- **OpenAI** (GPT family)
- **Google** (Gemini family)
- **Meta** (Llama family)
- **Mistral**
- **DeepSeek**
- **xAI** (Grok)
- And many more (60+ total)

### Notable Models
| Model | Category |
|---|---|
| Claude Opus 4.6 | Premium (1M context) |
| Claude Sonnet 4.6 | Mid-range frontier |
| GPT-4o, GPT-4.5 | Premium |
| Gemini 3.1 Pro | Premium (1M context) |
| DeepSeek R1 | Free tier |
| Llama 3.3 70B | Free tier |
| Gemma 3 | Free tier |

Switching between models requires changing only one parameter — no code changes needed.

Browse all models: https://openrouter.ai/models

---

## Pricing

### Tiers
| Tier | Description |
|---|---|
| **Free** | Dozens of free models, rate-limited (typically 20 req/min, 200/day) |
| **Pay-as-you-go** | Pre-purchase credits, use across all models |
| **Enterprise** | Volume discounts, annual commits, invoicing |

### Key Pricing Details
- **No markup** — OpenRouter passes through provider pricing directly
- **Per-token billing** — Input and output tokens priced separately
- **Credit purchase fees** — 5.5% on credit card (min $0.80); 5% on crypto (no minimum)
- **BYOK fee** — 5% on upstream usage when using your own API keys
- **Payment methods** — Credit/debit cards, crypto (USDC), bank transfers
- **Credit expiry** — No expiration on credits
- **Refunds** — Available within 24 hours of purchase for unused credits
- **Free tier caps** — 50 requests/day, 20 requests/min; purchasing 10+ credits raises free-model cap to 1,000 requests/day

Detailed pricing: https://openrouter.ai/pricing

---

## API Quick Start

### Python (using OpenAI SDK)

```python
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="your-openrouter-api-key",
)

response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4-6",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
)

print(response.choices[0].message.content)
```

### TypeScript/JavaScript (using OpenAI SDK)

```bash
npm i openai
```

```typescript
import OpenAI from "openai";

const client = new OpenAI({
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: "your-openrouter-api-key",
});

const response = await client.chat.completions.create({
    model: "anthropic/claude-sonnet-4-6",
    messages: [
        { role: "user", content: "Hello!" }
    ],
});

console.log(response.choices[0].message.content);
```

### cURL

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer your-openrouter-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-sonnet-4-6",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

---

## Considerations & Limitations

| Consideration | Details |
|---|---|
| **Added latency** | Typically ~15ms overhead under normal conditions, but can be 200–500ms+ under load; during peak events (e.g., Black Friday 2025), p99 latency reportedly hit 10 seconds |
| **Free tier limits** | 50 requests/day, 20 requests/min without credits |
| **No volume discounts** on pay-as-you-go | Volume pricing is enterprise-only |
| **Credit purchase fees** | 5.5% on credit card, 5% on crypto — compounds at high volume |
| **No public SLAs** | No published uptime guarantees; enterprise customers must negotiate terms individually |
| **Dynamic pricing risk** | Model pricing and availability can change; some users have reported unexpected cost spikes |
| **No semantic caching** | Repeated identical requests are billed at full price |
| **Extra data hop** | Every request routes through OpenRouter's infrastructure, which may be a concern for strict GDPR/HIPAA/data residency requirements |
| **Support** | Primarily via Discord rather than traditional support channels |
| **Quality variance** | ~5% output quality variance and ~15% more hallucinations reported on niche domains when using cost-optimized routing |

---

## Documentation Links

| Resource | URL |
|---|---|
| Homepage | https://openrouter.ai/ |
| Quickstart Guide | https://openrouter.ai/docs/quickstart |
| API Reference | https://openrouter.ai/docs/api/reference/overview |
| Models | https://openrouter.ai/models |
| Pricing | https://openrouter.ai/pricing |
| OpenAI SDK Guide | https://openrouter.ai/docs/guides/community/openai-sdk |
| Authentication | https://openrouter.ai/docs/api/reference/authentication |
| Responses API (Beta) | https://openrouter.ai/docs/api/reference/responses/overview |
| FAQ | https://openrouter.ai/docs/faq |
| Providers | https://openrouter.ai/providers |
| Provider Routing | https://openrouter.ai/docs/guides/routing/provider-selection |
| Tool Calling | https://openrouter.ai/docs/guides/features/tool-calling |

---

## Additional SDK & Framework Support

Beyond the OpenAI SDK, OpenRouter integrates with:

- **OpenRouter native SDK** — `@openrouter/sdk` (TypeScript) with type-safe tool definitions and automatic multi-turn agentic loops
- **Vercel AI SDK** — via `@openrouter/ai-sdk-provider`
- **LangChain** and **LlamaIndex**
- **PydanticAI** and **Mastra**
- **Effect AI SDK**
- **Arize** (observability)

---

*Research compiled on 2026-03-02*
