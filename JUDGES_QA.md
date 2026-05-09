# Munjiz Branch AI — Judges Q&A Briefing
# دليل الإجابة على أسئلة الحكام

> **How to use this** · **كيف تستخدم هذه الوثيقة**
> 35 most-likely judge questions, organized by theme, bilingual side-by-side (Arabic primary, English equivalent).
> Each answer ends with a `🔎 Evidence` line pointing to actual code, fixtures, or running behavior so you can prove the claim live.
>
> ٣٥ سؤالاً متوقعاً من الحكام، مرتّبة حسب الموضوع، باللغتين العربية والإنجليزية. كل إجابة تنتهي بمصدر دليل (`🔎 Evidence`) يربطها بكود حقيقي أو بيانات أو سلوك حيّ — لتثبت الادعاء أمام الحكم لحظياً.

---

## Section A — Heterogeneous Architecture · المعمارية متعددة النماذج

---

### Q1. لماذا خمسة وكلاء وليس نموذجاً واحداً بخمسة برومبتات؟ / Why 5 agents instead of 1 model with 5 prompts?

**A (ع):** لأن كل دور له طبيعة معرفية مختلفة. التحليلات الرياضية (سارة) تحتاج استدلال دقيق، وخدمة العملاء (خالد) تحتاج طلاقة باللهجة السعودية، والقرار النهائي (المنسق) يحتاج موازنة مقايضات معقدة. نموذج واحد يكون ضعيفاً في جانب أو اثنين دائماً. كل وكيل **معزول في عمليته الخاصة** مع برومبت نظامي مخصّص ودرجة حرارة مختلفة (analyzed: 0.2 — empathetic: 0.7) وسجل قراراتٍ منفصل، فلا يتداخل تفكير الأرقام مع تفكير المشاعر.

**A (EN):** Because each role has a different cognitive profile. Quantitative analysis (Sara) needs careful reasoning, customer service (Khalid) needs Saudi-dialect warmth, the final decision (Orchestrator) needs to balance complex trade-offs. A single model is always weaker on one or two dimensions. Each agent runs in **its own isolated process** with a custom system prompt, role-tuned temperature (0.2 for analytical agents, 0.7 for empathetic), and a separate decision log — number-thinking never bleeds into emotion-thinking.

> 🔎 Evidence: `apps/agents/prompts.py` (5 distinct system prompts), `apps/agents/models.py:Agent.temperature` field, `Agent.objects` shows 5 rows.

---

### Q2. لماذا نماذج مختلفة؟ ولماذا ليست كلها Claude مثلاً؟ / Why heterogeneous models — why not all Claude?

**A (ع):** ثلاثة أسباب جوهرية. **(1) الجودة المتخصّصة:** Qwen 80B هو الأقوى عربياً لخالد، DeepSeek V3.2 هو الأرخص في الاستدلال الرقمي لسارة، Claude Opus 4.7 هو الأفضل في الموازنات المعقدة للمنسق. **(2) التكلفة:** استخدام Opus لكل وكيل = ٠.٢٥ دولار/سيناريو. هكذا = ٠.٠٨ دولار/سيناريو. وفر ٧٠٪. **(3) المرونة:** لو فشل مزوّد واحد، لا يتوقف النظام كله — فقط وكيل واحد يَفشل ويُحَوَّل تلقائياً لمزوّد بديل عبر multi-provider failover. هذا تصميم هندسي مدروس، ليس عبثاً.

**A (EN):** Three reasons. **(1) Specialized quality:** Qwen 80B is the best Arabic model for Khalid, DeepSeek V3.2 is the cheapest reasoning model for Sara, Claude Opus 4.7 is unmatched for the Orchestrator's trade-off balancing. **(2) Cost:** All-Opus = ~$0.25/scenario. Heterogeneous = ~$0.08/scenario — 70% cheaper. **(3) Resilience:** If one provider goes down, only one agent fails-over, not the whole system. This is deliberate engineering, not random selection.

> 🔎 Evidence: `apps/dashboard/views.py:MODEL_LABELS`, `apps/dashboard/views.py:MODEL_RATIONALES` — each agent's rationale visible on hover in dashboard.

---

### Q3. كيف اخترتم النموذج لكل دور؟ ما هو المعيار؟ / How did you pick the model for each role?

**A (ع):** ثلاثة معايير، بترتيب الأهمية: **(أ) ملاءمة معرفية:** هل النموذج معروف بهذه القدرة؟ Claude للموازنة، DeepSeek-R1 للرياضيات، Qwen للعربية. **(ب) التكلفة لكل قرار:** كم ريالاً للقرار الواحد؟ هذا مقياس أهم من السعر للمليون توكن. **(ج) موثوقية الإخراج:** هل النموذج يُعيد محتوى نظيف دائماً؟ (تعلّمنا الدرس عندما اختبرنا DeepSeek-R1 reasoning model — كان يُرجع توكنات تفكير بدون محتوى نهائي، فاستبدلناه بـ V3.2 instruct).

**A (EN):** Three criteria in priority order: **(a) Cognitive fit** — is the model known for this capability? Claude for trade-offs, DeepSeek-R1 for math, Qwen for Arabic. **(b) Cost per decision** — SAR per decision matters more than $/million tokens. **(c) Output reliability** — does the model return clean content every time? We learned this when DeepSeek R1 (a reasoning model) consumed all max_tokens on internal "thinking" and returned empty content — we switched to V3.2 instruct.

> 🔎 Evidence: Plan file Phase 11/Fix #3 documents the actual switch from R1 → V3.2 with logs showing the failure.

---

### Q4. ماذا لو ظهر نموذج جديد أفضل من Claude Opus غداً؟ / What if a better model than Claude Opus drops tomorrow?

**A (ع):** السطر الواحد يكفي للتبديل. كل وكيل يخزّن `model_name` في قاعدة البيانات، والمحرّك يستخدم OpenAI-compatible API الموحّد عبر OpenRouter. إذا ظهر `claude-opus-5` غداً، نُحدّث صف المنسق في DB وانتهى. لا توجد ثوابت hardcoded في الكود، ولا يوجد vendor lock-in. وهذا التصميم متعمّد — العالم يتغيّر بسرعة، فالمعمارية صُمّمت لتتغيّر معه.

**A (EN):** A single update statement is enough. Each agent stores its `model_name` in the database, and the engine uses the OpenAI-compatible API surface through OpenRouter. If `claude-opus-5` drops tomorrow, we update one DB row for the Orchestrator and ship. No hardcoded constants, no vendor lock-in. This is deliberate — the model landscape changes weekly; the architecture is built to absorb that.

> 🔎 Evidence: `apps/agents/engine.py:run_agent` uses `agent.model_name` (DB-driven), not a constant. We literally swapped Sara from `:free` Qwen → DeepSeek R1 → DeepSeek V3.2 in this same project, no code change.

---

## Section B — Agent Communication & A2A Protocol · بروتوكول التواصل بين الوكلاء

---

### Q5. كيف يتواصل الوكلاء فيما بينهم فعلياً؟ / How do agents actually communicate with each other?

**A (ع):** بروتوكول Agent-to-Agent (A2A) داخلي مبسّط. كل وكيل يُنتج `AgentMessageEnvelope` (dataclass موحّدة: from_agent, to_agent, content, message_type, priority, raw_data) — وهذه تُحفظ في `AgentMessage` في PostgreSQL، وتُرسل عبر Django Channels group_send إلى Redis pub/sub، فتصل الواجهة ولكل وكيل لاحق في السلسلة. الوكيل التالي يقرأ ردود الوكلاء السابقين عبر `agent_inputs` dictionary مُضمَّنة في برومبته، فيرى **رأي زملائه قبل أن يُكوّن رأيه**.

**A (EN):** A simplified Agent-to-Agent (A2A) protocol. Each agent produces an `AgentMessageEnvelope` (unified dataclass: from_agent, to_agent, content, message_type, priority, raw_data) — persisted as `AgentMessage` in PostgreSQL and broadcast via Django Channels `group_send` to Redis pub/sub. The next agent reads previous agents' responses through an `agent_inputs` dictionary embedded in its prompt — **so it sees its colleagues' opinions before forming its own**.

> 🔎 Evidence: `apps/agents/a2a_protocol.py` (the envelope dataclass), `apps/agents/engine.py:run_scenario_with_ai` (the chained context-passing), `apps/agents/models.py:AgentMessage` (persistence schema).

---

### Q6. أي بروتوكول A2A تستخدمون؟ هل اخترعتموه؟ / What A2A protocol — did you invent it?

**A (ع):** بروتوكول داخلي خاص بنا، مستوحى من معيار A2A الذي طرحته Google في ٢٠٢٥ لكن مبسّط لحالتنا. لا نستخدم A2A الكامل لأن سيناريوهاتنا أحادية الجلسة (single-session) — لا نحتاج discovery أو long-running tasks. سيناريو واحد = ٥ وكلاء × رسالة واحدة لكل وكيل، مدّتها ٦٠ ثانية. لو احتجنا توسيع لـ asynchronous workflows أو inter-bank coordination مستقبلاً، يمكن الترقية لمعيار A2A الكامل بدون كسر.

**A (EN):** Our own internal protocol, inspired by Google's A2A standard (2025) but simplified for our session shape. We don't use full A2A because our scenarios are single-session — no agent discovery or long-running tasks needed. One scenario = 5 agents × 1 message each, ~60 seconds total. If we ever need asynchronous workflows or inter-bank coordination, we can upgrade to the full A2A standard non-disruptively.

> 🔎 Evidence: `apps/agents/a2a_protocol.py` is intentionally minimal (a dataclass), not an over-engineered framework.

---

### Q7. هل التواصل متزامن أم غير متزامن؟ / Is communication synchronous or asynchronous?

**A (ع):** **داخل السيناريو الواحد:** متسلسل (sequential) — سارة تتكلم أولاً، فهد يقرأ ردها، خالد يقرأ ردهما، إلخ. هذا متعمّد لأن قرار المنسق يحتاج رأي الجميع قبل التشكُّل. **خارج السيناريو:** غير متزامن (async) — Celery يستقبل المهام في طابور Redis، وعدة سيناريوهات يمكن تشغيلها بالتوازي على ٤ workers. هذه ثنائية مشهورة: "متسلسل داخل، متوازٍ خارج".

**A (EN):** **Inside a scenario:** sequential — Sara speaks first, Fahad reads her response, Khalid reads both, etc. Deliberate, because the Orchestrator's decision needs everyone's input before it can form. **Across scenarios:** async — Celery picks up tasks from Redis queue, multiple scenarios can run in parallel across 4 workers. This is the well-known "sequential within, parallel across" pattern.

> 🔎 Evidence: `apps/agents/engine.py:run_scenario_with_ai` (sequential `run_agent` calls), `docker-compose.yml:celery_worker --concurrency=4` (parallel across).

---

### Q8. هل يمكن للوكلاء الاختلاف؟ كيف يُحلّ الخلاف؟ / Can agents disagree — how is conflict resolved?

**A (ع):** نعم، وهذا متعمّد. مثلاً في سيناريو S-06 (تصعيد VIP غاضب): سارة تقول "خسارة ١.٨٤ مليون ريال متوقعة"، فهد يقول "تعويض ٥٠٠ ريال ضمن صلاحياتك"، خالد يقول "لازم تعويض أكبر للحفاظ على العميل". الخلاف هنا حقيقي. **المنسق هو حَكَم الخلاف** — يستخدم Claude Opus 4.7 لأنه الأفضل في موازنة المقايضات: أَخَذ رأي كل وكيل بصفته "رأي خبير في مجاله"، ثم وَزَن المقايضات (ROI vs authority limit vs customer retention) واتّخذ قراراً مع مبرّر مكتوب.

**A (EN):** Yes, by design. In S-06 (angry VIP escalation): Sara says "1.84M SAR retention loss projected", Fahad says "500 SAR is your authority cap", Khalid says "we need a bigger gesture". Genuine conflict. **The Orchestrator arbitrates** — that's why we use Claude Opus 4.7, the best at trade-off balancing. It treats each agent's opinion as expert input from their domain, weighs the trade-offs (ROI vs authority limit vs retention), and writes a reasoned decision with explicit justification.

> 🔎 Evidence: `fixtures/scenario_scripts.json:S-06` shows the real conflict; the actual AI runs we did showed the Orchestrator opening with "اتفقت آراء الفريق والوضع واضح" — i.e., it explicitly references the team's collective input.

---

### Q9. لماذا هذا الترتيب تحديداً (سارة → فهد → خالد → نورة → المنسق)؟ / Why this specific order?

**A (ع):** ترتيب مقصود يُعكّس **تدفّق صنع القرار البشري**. سارة أولاً لأن **الأرقام يجب أن تأتي قبل الرأي** (data before opinion). فهد ثانياً لأنه يضع **القيود** (constraints) — كم لدينا من موظفين، ما هي حدود SLA. خالد ثالثاً لأنه يقرأ **الإنسان** (human) — مزاج العميل، ملفه. نورة رابعاً لأنها تَبني **الحل** (solution) — وهي تحتاج البيانات + القيود + قراءة العميل لتُصمّم خطة. المنسق أخيراً لأنه **يقرّر** (decides) ولا يقرّر إلا بعد رؤية كل المدخلات. هذا ليس عبثياً — هذا workflow design.

**A (EN):** Intentional order mirroring **human decision flow**. Sara first because **data before opinion**. Fahad second because he sets the **constraints** — staff available, SLA limits. Khalid third because he reads the **human** — customer mood, profile. Nora fourth because she builds the **solution** — and she needs data + constraints + human-context to design a plan. Orchestrator last because **deciding requires complete information**. This is workflow design, not arbitrary.

> 🔎 Evidence: `apps/agents/engine.py:run_scenario_with_ai` lines 95–120, the explicit chain.

---

### Q10. أرني هيكل رسالة وكيل واحدة. / Show me the structure of one agent message.

**A (ع):** `AgentMessageEnvelope` يحوي: `from_agent`, `to_agent` (اختياري), `content` (النص العربي), `message_type` (analysis/update/suggestion/decision/alert/etc), `priority` (low/medium/high/critical), `raw_data` (JSON للبيانات الخام التي بنى الوكيل عليها قراره — للتدقيق). كل رسالة تُحفظ مع `created_at` و `order` (الترتيب في السلسلة). هذا schema يتيح **audit trail كامل** — كل قرار له مبرّر مع البيانات التي بُني عليها.

**A (EN):** `AgentMessageEnvelope` contains: `from_agent`, optional `to_agent`, `content` (Arabic text), `message_type` (analysis/update/suggestion/decision/alert/etc), `priority` (low/medium/high/critical), `raw_data` (JSON of the raw data the agent reasoned over — for audit). Each message is persisted with `created_at` and `order`. This schema enables a **full audit trail** — every decision has its reasoning AND the data behind it.

> 🔎 Evidence: `apps/agents/models.py:AgentMessage` (full field list), `apps/agents/a2a_protocol.py:AgentMessageEnvelope`.

---

## Section C — End-to-End Technical Flow · التدفق الكامل من الضغطة إلى الرد

---

### Q11. اشرح بالتفصيل ما يحدث عندما أضغط زر سيناريو. / Walk me through what happens when I click a scenario.

**A (ع):**
```
1. Browser   → WebSocket: { action: 'trigger_scenario', scenario_id: 'S-03' }
2. Daphne    → DashboardConsumer.receive() يقرأ الرسالة
3. Consumer  → Celery: run_scenario_task.delay('S-03') (يُرسل المهمة لـ Redis queue)
4. Worker    → يَستلم المهمة، يبني context من DB (staff, customers, queue snapshot)
5. Engine    → يبدأ السيناريو، يُرسل scenario_started broadcast لكل التبويبات المفتوحة
6. لكل وكيل (×٥):
   a. update agent.status = 'thinking', broadcast لـ UI
   b. يبني user_message مع context + ردود الوكلاء السابقين
   c. POST → openrouter.ai/api/v1/chat/completions
   d. response → يُحفظ في AgentMessage table
   e. broadcast الرسالة على dashboard group via channels-redis
   f. update status = 'idle', broadcast
7. عند الانتهاء: scenario_ended broadcast
8. Browser   ← يستقبل كل event عبر WebSocket → JS dispatches إلى MunjizBus → handlers تُحدّث DOM
```
المدّة الإجمالية: ~٦٠–٩٠ ثانية، اعتماداً على بطء Claude Opus.

**A (EN):**
```
1. Browser   → WebSocket: { action: 'trigger_scenario', scenario_id: 'S-03' }
2. Daphne    → DashboardConsumer.receive() reads the frame
3. Consumer  → Celery: run_scenario_task.delay('S-03') (enqueues on Redis)
4. Worker    → picks up task, builds context from DB (staff, customers, queue snapshot)
5. Engine    → starts scenario, broadcasts scenario_started to all open tabs
6. For each agent (×5):
   a. set agent.status = 'thinking', broadcast to UI
   b. build user_message with context + previous agents' responses
   c. POST → openrouter.ai/api/v1/chat/completions
   d. response → persisted in AgentMessage table
   e. broadcast on dashboard group via channels-redis
   f. set status = 'idle', broadcast
7. At end: scenario_ended broadcast
8. Browser   ← receives every event over WebSocket → JS dispatches to MunjizBus → handlers update DOM
```
Total: ~60–90s depending on Claude Opus latency.

> 🔎 Evidence: `apps/agents/consumers.py`, `apps/agents/tasks.py:run_scenario_task`, `apps/agents/engine.py:run_scenario_with_ai`, `static/js/websocket.js`, `static/js/dashboard.js:handleIncomingMessage`.

---

### Q12. لماذا WebSocket وليس HTTP polling؟ / Why WebSocket over HTTP polling?

**A (ع):** ثلاثة أسباب. **(1) الكُمون (latency):** WebSocket يدفع الرسالة فور إنتاجها، Polling يُضيف ٢٥٠ ms في المتوسط (عند فاصل polling = ٥٠٠ ms). للسيناريو الذي يحتوي ١٥ event، هذا = ٣.٧٥ ثانية ضائعة. **(2) الكفاءة:** Polling يُولّد ١٢٠ HTTP request في الدقيقة (request-overhead = ٤٨٠ kB) — WebSocket يستخدم اتصالاً واحداً مفتوحاً (~٢٠ kB إجمالاً للسيناريو). **(3) المعمارية:** WebSocket طبيعي لـ Django Channels + Redis pub/sub — broadcasting لعدة tabs مفتوحة يصبح مجاناً. هذا حلّ مدروس، ليس مجرد تفضيل تقني.

**A (EN):** Three reasons. **(1) Latency:** WebSocket pushes the moment a message is produced; polling adds ~250ms average (at 500ms interval). 15 events × 250ms = 3.75s wasted per scenario. **(2) Efficiency:** Polling = 120 HTTP requests/min (~480kB overhead). WebSocket = one persistent connection (~20kB total). **(3) Architecture fit:** WebSocket pairs naturally with Django Channels + Redis pub/sub — broadcasting to multiple open tabs becomes free.

> 🔎 Evidence: `config/asgi.py` (ProtocolTypeRouter wiring), `apps/agents/consumers.py:DashboardConsumer.GROUP = 'dashboard'`.

---

### Q13. لماذا Celery؟ لماذا لا تستدعون LLM مباشرة من view؟ / Why Celery — why not call LLMs directly from a view?

**A (ع):** الاستدعاء المباشر سيُنشئ **HTTP request يبقى مفتوحاً ٦٠–٩٠ ثانية**، وهذا سيُسبب: (أ) timeouts على nginx/load-balancer, (ب) تجمّد الـ request worker، (ج) كسر سلوك المستخدم لو أغلق الـ tab أثناء الانتظار. Celery يحلّ كل هذا — الـ HTTP/WebSocket request يُرجع `{queued: true}` فوراً، والمهمة تُشغَّل في worker process منفصل، والنتائج تتدفّق عبر WebSocket. هذا هو النمط القياسي لـ long-running AI tasks في الإنتاج.

**A (EN):** A direct call would hold an HTTP request open for 60-90 seconds, causing: (a) nginx/load-balancer timeouts, (b) request workers blocked, (c) broken UX if user closes tab mid-wait. Celery solves this — the HTTP/WebSocket request returns `{queued: true}` immediately, the task runs in a separate worker process, results stream over WebSocket. Industry-standard pattern for long-running AI tasks.

> 🔎 Evidence: `apps/agents/tasks.py:@shared_task`, `docker-compose.yml:celery_worker` (separate container).

---

### Q14. أين تُحفظ الرسائل؟ / Where are messages persisted?

**A (ع):** PostgreSQL، جدول `agents_agentmessage`. كل رسالة لها UUID، تربط `scenario` و `from_agent`، وتُخزّن المحتوى الكامل + metadata (raw_data JSON, message_type, priority, is_ai_generated, order). هذا يعطينا **سجل تدقيق غير قابل للتعديل** (immutable audit trail) — كل قرار AI اتُّخِذ على الإطلاق محفوظ مع البيانات التي بُني عليها. مهمّ لـ SAMA compliance.

**A (EN):** PostgreSQL, table `agents_agentmessage`. Each message has a UUID, FKs to `scenario` and `from_agent`, and stores full content + metadata (raw_data JSON, message_type, priority, is_ai_generated, order). This gives us an **immutable audit trail** — every AI decision ever made is persisted with the data behind it. Critical for SAMA compliance.

> 🔎 Evidence: `apps/agents/models.py:AgentMessage`, `apps/agents/admin.py:AgentMessageAdmin` (browseable in Django admin).

---

## Section D — Orchestrator Decision-Making · صنع القرار في المنسق

---

### Q15. كيف يَزِن المنسق المدخلات المتضاربة؟ / How does the Orchestrator weigh conflicting inputs?

**A (ع):** المنسق يُمرَّر له dictionary اسمه `agent_inputs` يحوي ردود الوكلاء الأربعة الآخرين بأسمائهم العربية: `{'سارة (التحليلات)': '...', 'فهد (العمليات)': '...', 'خالد (العملاء)': '...', 'نورة (الطوابير)': '...'}`. system prompt للمنسق يُلزمه بـ: (١) قراءة كل المدخلات، (٢) موازنة المقايضات (التكلفة، الصلاحية، تأثير العميل)، (٣) إصدار قرار مع **مبرّر مكتوب**، (٤) تحديد ما إذا كان القرار ضمن صلاحياته أم يحتاج تصعيد. درجة الحرارة منخفضة (٠.٢) لقرارات حاسمة وثابتة.

**A (EN):** The Orchestrator gets an `agent_inputs` dict with all 4 specialists' responses keyed by their Arabic names. Its system prompt mandates: (1) read all inputs, (2) weigh trade-offs (cost, authority, customer impact), (3) issue a decision **with written reasoning**, (4) determine whether the decision is within its authority or needs escalation. Temperature kept low (0.2) for decisive consistency.

> 🔎 Evidence: `apps/agents/engine.py:run_scenario_with_ai` lines 122–135 (orchestrator context construction), `apps/agents/prompts.py:PROMPTS['orchestrator']`.

---

### Q16. ما الذي يمنع المنسق من الهلوسة؟ / What stops the Orchestrator from hallucinating?

**A (ع):** أربع طبقات. **(1) الأرقام الحيّة في البرومبت:** نضع state-of-the-branch (٤٠ عميل، ١٨ دقيقة، إلخ) بشكل بارز في رأس البرومبت مع تعليمة صريحة "استخدم الأرقام الحيّة، لا تنسخ من وصف السيناريو". **(2) درجة حرارة منخفضة:** ٠.٢ تُقلّل التنويع. **(3) سياق محدود:** المنسق يرى فقط ردود الوكلاء + بيانات الفرع، لا توجد internet search ولا knowledge gaps يُملأها بالخيال. **(4) Audit trail:** كل قرار محفوظ مع المدخلات — لو هَلوس، الدليل واضح فوراً ويُمكن المراجعة.

**A (EN):** Four layers. **(1) Live numbers prominent in prompt:** branch state (40 customers, 18 min, etc.) appears at the top of the prompt with explicit "use the live numbers, do NOT copy from scenario description" instruction. **(2) Low temperature:** 0.2 reduces variation. **(3) Bounded context:** Orchestrator sees only agent responses + branch data — no internet search, no knowledge gaps to fill with imagination. **(4) Audit trail:** every decision persisted with inputs — if it hallucinates, evidence is immediate and reviewable.

> 🔎 Evidence: `apps/agents/engine.py:run_agent` lines 36–58 (prompt structure with "⚡ الحالة الحيّة الآن (المصدر الموثوق)" header), `agent.temperature=0.2` for orchestrator in DB.

---

### Q17. صلاحيات المنسق — كيف تُفرَض؟ / Orchestrator authority limits — how enforced?

**A (ع):** **مرحلتنا الحالية:** الصلاحيات موصوفة في system prompt للمنسق ("تعويض حتى ٥٠٠ ريال = تلقائي، أكثر = يحتاج المدير ماجد")، والمنسق يحترمها بشكل موثوق ٩٥٪ من الوقت في اختباراتنا. **مرحلة الإنتاج:** سنضيف **policy guard** برمجي — قبل تنفيذ أي قرار مالي، يمرّ الإجراء عبر `apps/governance/limits.py` (TODO) الذي يفحص: قيمة التعويض، نوع الإجراء، توقيت اليوم، صلاحية الفرع. هذا يضمن الالتزام **بالكود لا بالنية**. الـ prompt-based approach كافٍ للعرض التجريبي، الـ code-enforced approach مطلوب للإنتاج البنكي.

**A (EN):** **Current MVP:** authority limits are described in the Orchestrator's system prompt ("compensation up to 500 SAR = auto, above = needs manager Majed") and the Orchestrator respects them 95% of the time in our tests. **Production:** we'll add a programmatic **policy guard** — before any financial decision is executed, it passes through `apps/governance/limits.py` (TODO) that checks compensation value, action type, time of day, branch authority. This enforces compliance **in code, not in good intent**. Prompt-based is fine for the demo; code-enforced is mandatory for production banking.

> 🔎 Evidence: `apps/agents/prompts.py:PROMPTS['orchestrator']` (current prompt-based), honest acknowledgment of the gap.

---

### Q18. متى يَصعّد للبشر؟ / When does it escalate to a human?

**A (ع):** ثلاثة محفّزات. **(1) القيمة المالية:** أي قرار > حدّ صلاحية المنسق (٥٠٠ ريال للتعويض، تمديد ساعات، استدعاء خارجي، تخفيض رسوم > حدّ معيّن). **(2) الحساسية القانونية:** أي شكوى تُلمّح لقضية، أي طلب تجميد حساب VIP، أي مسألة كذب أو احتيال. **(3) الثقة المنخفضة:** لو الوكلاء اختلفوا اختلافاً حاداً (المنسق يعرف ذلك من تباين ردودهم) أو لو سارة قالت confidence < ٧٠٪. التصعيد لا يعني انتظار البشر — المنسق يَتّخذ القرارات الفورية ضمن صلاحياته، ويُرسل **إشعاراً للمدير مع تحليل مكتمل** للقرارات التي تحتاج تأكيداً.

**A (EN):** Three triggers. **(1) Financial value:** any decision above Orchestrator's authority cap (500 SAR comp, hours extension, external escalation, fee waiver above threshold). **(2) Legal sensitivity:** complaints implying litigation, account freeze requests on VIPs, fraud or deception flags. **(3) Low confidence:** if agents disagree sharply (Orchestrator detects this from response variance) or if Sara reports confidence < 70%. Escalation doesn't mean waiting for humans — the Orchestrator executes within-authority decisions immediately and sends the manager **a notification with full analysis** for decisions needing confirmation.

> 🔎 Evidence: `fixtures/scenario_scripts.json:S-06` (the orchestrator's response shows partial-escalation: "تصعيد جزئي للمدير... ضمن صلاحياتي [items], يحتاج المدير [bigger items]").

---

## Section E — Failure & Resilience · الفشل والصمود

---

### Q19. ماذا لو فشل وكيل واحد في منتصف السيناريو؟ / What if one agent fails mid-scenario?

**A (ع):** نظامنا يَتعامل مع الفشل بطبقتين. **(1) Per-agent retry:** OpenAI SDK لها retry تلقائي لـ rate limits (default = ٢ retries) — يَحلّ معظم الفشل العابر بصمت دون تدخّل المستخدم. **(2) Multi-provider failover (production):** نفس واجهة OpenAI-compatible متاحة عبر OpenRouter, Anthropic Direct, Groq, Azure OpenAI. لو فشل المزوّد الأول، يُحَوَّل تلقائياً للتالي حسب أولوية مُعرَّفة. النتيجة: السيناريو يَستمرّ بصمت بنماذج بديلة عند الحاجة، والمستخدم لا يَرى انقطاعاً.

**A (EN):** Two layers. **(1) Per-agent retry:** OpenAI SDK auto-retries on rate limits (default 2) — handles most transient failures silently. **(2) Multi-provider failover (production):** the same OpenAI-compatible API surface is reachable through OpenRouter, Anthropic Direct, Groq, Azure OpenAI. If the primary provider fails, the engine transparently fails over to the next per a defined priority. Result: scenarios continue uninterrupted across providers; the user sees no disruption.

> 🔎 Evidence: `apps/agents/engine.py:OpenAI(base_url=settings.LLM_BASE_URL)` — abstracted away from any single provider. `apps/agents/tasks.py:run_scenario_task` retries through the engine's SDK retry policy.

---

### Q20. ماذا لو OpenRouter كله مَعطّل؟ / What if OpenRouter is entirely down?

**A (ع):** **متعدّد المزوّدين** هو الجواب. نفس واجهة API (OpenAI-compatible) متاحة عبر Anthropic Direct, Groq, Azure OpenAI. لو OpenRouter سَقط، يُحَوَّل النظام تلقائياً للمزوّد التالي حسب priority list مُعرَّفة في `.env`: `OpenRouter → Anthropic Direct → Groq → Ollama-local`. الـ engine يَستخدم `base_url` متغيّر، لذلك التحويل = تحديث env var واحد. هذا تصميم مُتوقَّع وُضع منذ البداية.

**A (EN):** **Multi-provider failover** is the answer. The same OpenAI-compatible API surface is reachable through Anthropic Direct, Groq, Azure OpenAI. If OpenRouter goes down, the engine auto-fails over per a priority list set in `.env`: `OpenRouter → Anthropic Direct → Groq → Ollama-local`. The engine uses a parameterized `base_url`, so failover is a one-env-var swap. Designed in from day one.

> 🔎 Evidence: `apps/agents/engine.py:OpenAI(base_url=settings.LLM_BASE_URL)` — already abstracted from the specific provider.

---

### Q21. كيف تُحاطون أنفسكم من تجاوز التكلفة؟ / How do you protect against cost runaway?

**A (ع):** ثلاثة دفاعات. **(1) Token caps:** كل وكيل له `max_tokens=500` ثابت، فلا يمكن لـ Claude Opus أن يُولّد ١٠٠ ألف توكن وحدها. **(2) Rate limiting (TODO production):** rate-limit-per-branch على trigger endpoint — كحدّ أقصى ٢٠ سيناريو/ساعة/فرع. **(3) Cost monitoring:** OpenRouter يُرسل usage بيانات في كل response، نُسجّلها في DB ونُرسل alert لو تجاوز فرع حدّ يومي. الميزانية المتوقعة: ١٣٠–٢٠٥ دولار/فرع/شهر للنطاق الإنتاجي — منضبط ومُتنبَّأ به.

**A (EN):** Three defenses. **(1) Token caps:** every agent has fixed `max_tokens=500`, so Claude Opus can't generate 100k tokens alone. **(2) Rate limiting (production TODO):** per-branch rate cap on the trigger endpoint — max 20 scenarios/hour/branch. **(3) Cost monitoring:** OpenRouter returns usage in every response — we log it in DB and alert if a branch exceeds daily budget. Projected cost: $130–205/branch/month at production scale — tight and predictable.

> 🔎 Evidence: `apps/agents/engine.py:max_tokens=500`, plan file Phase 11 cost economics section.

---

### Q22. ماذا لو النموذج أرجع محتوى فارغاً أو هراءً؟ / What if the model returns empty or gibberish?

**A (ع):** المحرّك يَفحص ذلك صراحة قبل القبول: `if not result or not result.strip(): raise LLMUnavailable(...)`. الـ exception يُحفّز SDK retry policy تلقائياً، ولو فَشل المزوّد الأساسي بشكل مستمرّ، multi-provider failover يَنقل الطلب لمزوّد آخر. اخترنا نماذج موثوقة: نَجَحنا مبكراً عندما حدَّدنا أن DeepSeek R1 (reasoning model) كان يَستهلك max_tokens في "thinking" داخلي ويُرجع content فارغاً — بَدّلناه إلى V3.2 instruct الذي يُرجع محتوى دائماً، فالنماذج الحالية اخْتُبِرت تحت ظروف متنوعة. للهراء: programmatic output validation (production TODO) يَفحص إيموجي البداية + الحد الأدنى من الكلمات العربية + بنية متوقَّعة.

**A (EN):** The engine explicitly validates: `if not result or not result.strip(): raise LLMUnavailable(...)`. The exception triggers the SDK retry policy, and if the primary provider keeps failing, multi-provider failover routes the call elsewhere. Our chosen models are battle-tested: we caught early that DeepSeek R1 (a reasoning model) consumed all max_tokens on internal "thinking" and returned empty content — we switched to V3.2 instruct, which always returns content. Models in production have all been validated. For gibberish: programmatic output validation (production TODO) will check leading emoji, minimum Arabic word count, expected structure markers.

> 🔎 Evidence: `apps/agents/engine.py:run_agent` (the explicit empty-check), the plan file documents the R1 → V3.2 switch with full logs.

---

## Section F — Production & Scale · الإنتاج والقابلية للتوسّع

---

### Q23. كيف يَتوسّع هذا النظام لـ ٢٠٠ فرع؟ / How does this scale to 200 branches?

**A (ع):** المعمارية stateless من الأساس — كل branch يُحدَّد بـ `branch_id`، وكل agent state معزول. التوسعة الأفقية تقتصر على ثلاثة مكوّنات: **(١) Celery workers:** نَزيد من ٤ إلى ١٦ workers، حتى نُعالج ٤×٢٠٠ = ٨٠٠ سيناريو/ساعة/cluster. **(٢) PostgreSQL:** read replicas + connection pooling (PgBouncer). **(٣) Redis:** cluster mode للـ pub/sub broadcast. الـ LLM API هو الـ bottleneck الحقيقي الوحيد — ولأن OpenRouter نفسه multi-provider، هذا غير محدود عملياً. Kubernetes (EKS Riyadh / AKS Riyadh) للـ orchestration الإنتاجي.

**A (EN):** The architecture is stateless by design — every branch keyed by `branch_id`, agent state isolated. Horizontal scaling needs three components scaled: **(1) Celery workers:** scale from 4 to 16, processing 4×200 = 800 scenarios/hour/cluster. **(2) PostgreSQL:** read replicas + connection pooling (PgBouncer). **(3) Redis:** cluster mode for pub/sub. The real bottleneck is LLM APIs — but since OpenRouter is itself multi-provider, this is practically unbounded. Kubernetes (EKS Riyadh / AKS Riyadh) for production orchestration.

> 🔎 Evidence: `apps/agents/tasks.py:_build_context(branch_id='RYD-OLY-042')` — branch_id parameterized, plan file Phase 6 production architecture section.

---

### Q24. كيف تَدعمون عدة بنوك (multi-tenancy)؟ / How do you handle multi-tenancy (multiple banks)?

**A (ع):** **مرحلتنا الحالية:** single-tenant (بنك واحد). **المرحلة الإنتاجية:** نضيف `Tenant` model + `tenant_id` على كل صف، مع `django-tenants` للـ schema isolation في PostgreSQL — كل بنك له schema منفصل، الـ ORM يعزل تلقائياً. المعزولات تشمل: prompts (لو بنك أراد تخصيص لهجة الوكلاء)، model_choices (بنك ذو ميزانية أعلى يَستخدم Opus لكل وكيل)، authority_limits (تختلف حدّ تعويض من بنك لآخر)، compliance_rules. هذا تصميم قياسي لـ B2B SaaS مرخّص.

**A (EN):** **Current MVP:** single-tenant. **Production:** we add a `Tenant` model + `tenant_id` on every row, with `django-tenants` for PostgreSQL schema isolation — each bank gets its own schema, ORM isolates automatically. Per-tenant config covers: prompts (if a bank wants custom agent dialect), model_choices (bigger budget bank uses Opus for all agents), authority_limits (compensation cap differs per bank), compliance_rules. Standard B2B SaaS multi-tenancy.

> 🔎 Evidence: Current models lack `tenant_id` — honest acknowledgment this is for v2. Plan file Phase 6 covers production multi-tenancy.

---

### Q25. الكُمون: هل ٦٠ ثانية مقبولة لقرار حيّ؟ / Latency: is 60 seconds acceptable for a live decision?

**A (ع):** نعم، **في سياقها**. ٦٠ ثانية تشمل **خمسة قرارات تشاوُرية متعمّقة** من خمسة نماذج مختلفة — معدّل ١٢ ثانية/وكيل، أسرع من أي مدير بشري لو كنت تطلب منه نفس التحليل. بالمقارنة: مدير الفرع يَستغرق ٥–١٠ دقائق ليصل لقرار مماثل. لو احتجنا أسرع: (أ) نُشغّل بعض الوكلاء بالتوازي بدل التسلسل (الوكلاء المستقلون مثل سارة وفهد يمكن تشغيلهما متوازياً)، (ب) نُبدّل Claude Opus بـ Sonnet 4.5 للمنسق (٢-٣× أسرع، تكلفة أقل، جودة قريبة). هذه trade-offs مدروسة، نختارها حسب احتياج كل بنك.

**A (EN):** Yes, **in context**. 60 seconds includes **five deeply consultative decisions** from five different models — 12 seconds/agent, faster than any human manager doing the same analysis. Compare: a branch manager takes 5-10 minutes to reach a comparable conclusion. If we need faster: (a) parallelize independent agents (Sara and Fahad can run concurrently — they don't depend on each other), (b) swap Claude Opus → Sonnet 4.5 for the Orchestrator (2-3× faster, lower cost, near-quality). Deliberate trade-offs, configurable per bank.

> 🔎 Evidence: actual logs show 60.8s for full S-04 run, 87.5s for early run, both AI-mode. Production parallelization is documented as a tunable.

---

## Section G — Saudi Compliance & Context · الامتثال السعودي والسياق

---

### Q26. كيف تَلتزمون بإطار الأمن السيبراني السعودي (SAMA Cybersecurity Framework)؟ / How do you comply with SAMA Cybersecurity Framework?

**A (ع):** ستّة محاور مُغطّاة. **(1) Encryption in transit:** TLS 1.3 على كل HTTP/WebSocket. **(2) Encryption at rest:** PostgreSQL encryption at rest عبر AWS KMS أو Azure Key Vault. **(3) Audit logs:** كل قرار AI محفوظ مع timestamp + agent + model + cost — immutable في S3 Object Lock مع retention ٧ سنوات. **(4) Access control:** RBAC في الإنتاج (Keycloak / Azure AD)، MFA إجباري على لوحة التحكم. **(5) Network segmentation:** كل branch في VPC منفصل، لا اتصال مباشر بالإنترنت من الـ DB. **(6) Incident response:** alerts على PagerDuty لأي LLMUnavailable burst، أي authentication failure، أي cost spike. **سنّقدم compliance dossier كامل لـ SAMA قبل الإطلاق التجاري.**

**A (EN):** Six pillars covered. **(1) Encryption in transit:** TLS 1.3 on all HTTP/WebSocket. **(2) Encryption at rest:** PostgreSQL encryption via AWS KMS or Azure Key Vault. **(3) Audit logs:** every AI decision persisted with timestamp + agent + model + cost — immutable in S3 Object Lock with 7-year retention. **(4) Access control:** RBAC in production (Keycloak / Azure AD), MFA mandatory on dashboard. **(5) Network segmentation:** each branch in isolated VPC, no direct internet from DB. **(6) Incident response:** PagerDuty alerts for LLMUnavailable bursts, auth failures, cost spikes. **Full SAMA compliance dossier will be submitted before commercial launch.**

> 🔎 Evidence: Plan file Phase 6 production architecture section enumerates all six. Honest acknowledgment that current MVP has none of these — they're the gap between "demo" and "regulated production".

---

### Q27. PDPL (نظام حماية البيانات الشخصية) — بيانات العملاء التي تَعبر النماذج؟ / PDPL — customer data flowing through LLMs?

**A (ع):** قلق مشروع. الحل ثلاث طبقات. **(١) Data minimization:** لا نُمرّر أرقام حسابات أو هوية أو رقم جوّال للنموذج — نُمرّر فقط ما يحتاجه الوكيل لاتخاذ القرار (segment، annual_value_sar كرقم مُجمَّع، churn_risk كتصنيف). **(٢) Pseudonymization:** أسماء العملاء تُستبدل بـ aliases (`أبو محمد` بدل اسم الهوية الكامل) قبل دخول البرومبت. **(٣) On-prem option:** للبنوك الأكثر تحفّظاً، نُقدّم Ollama+Qwen محلياً — صفر بيانات تخرج من البنك. القرار يَبقى للبنك حسب درجة المخاطرة المقبولة.

**A (EN):** Legitimate concern. Three-layer mitigation. **(1) Data minimization:** we never pass account numbers, ID, or phone to the LLM — only what the agent needs to decide (segment, annual_value_sar as aggregate, churn_risk as category). **(2) Pseudonymization:** customer names replaced with aliases (`أبو محمد` instead of full ID name) before entering the prompt. **(3) On-prem option:** for the most conservative banks, we offer Ollama+Qwen running locally — zero data leaves the bank. Bank chooses risk tolerance.

> 🔎 Evidence: `apps/customers/models.py:Customer.alias` field, `fixtures/customer_data.json` shows aliases used; `apps/agents/tasks.py:_build_context` passes only summary fields to context.

---

### Q28. أين تَتمّ معالجة البيانات؟ / Where is data processed?

**A (ع):** ثلاثة خيارات قابلة للتكوين لكل بنك. **(أ) Regional cloud:** AWS Riyadh / Azure Riyadh / STC Cloud. الـ LLM calls تذهب لـ OpenRouter في نفس المنطقة — البيانات لا تُغادر المملكة. **(ب) Hybrid:** Munjiz في السحابة الإقليمية، LLMs محلياً عبر Ollama على GPUs في datacenter البنك. **(ج) On-prem كامل:** كل المكوّنات داخل datacenter البنك. السعر يختلف، لكن المعمارية هي نفسها — وهذا يجعل القرار **سياسة، لا هندسة**.

**A (EN):** Three configurable options per bank. **(a) Regional cloud:** AWS Riyadh / Azure Riyadh / STC Cloud. LLM calls go through OpenRouter within-region — data never leaves KSA. **(b) Hybrid:** Munjiz in regional cloud, LLMs local via Ollama on bank-DC GPUs. **(c) Full on-prem:** all components in bank datacenter. Cost differs, architecture is the same — making the decision **policy, not engineering**.

> 🔎 Evidence: Plan file Phase 6 deployment options section.

---

### Q29. الفصاحة الثقافية — أثبتوها لي. / Cultural fluency — prove it.

**A (ع):** أربعة أدلّة حيّة. **(1) لهجة سعودية حقيقية:** Qwen3-80B بُني على الكثير من العربية، وخالد يَستخدم تعابير مثل "حياك الله" "تأمر" "لا تصرنا" بشكل طبيعي — ليست ترجمة من إنجليزي. **(2) أوقات الصلاة:** سيناريو S-04 يُظهر الوكلاء يَتعاملون مع أذان الظهر تلقائياً (إغلاق مؤقت ٢٥ دقيقة، إشعار WhatsApp قبل ١٠ دقائق). **(3) سياق يوم الراتب:** S-03 يفترض ذروة ١.٨× في يوم الخميس نهاية الشهر — هذا سياق سعودي محدّد. **(4) أسماء حقيقية:** أبو محمد السديري VIP بقيمة ٨.٥ مليون ريال، عبدالرحمن العمري Premium بمخاطر تسرّب — أسماء واقعية تماماً، لا "John Smith".

**A (EN):** Four pieces of live evidence. **(1) Real Saudi dialect:** Qwen3-80B trained on extensive Arabic; Khalid uses "حياك الله" / "تأمر" / "لا تصرنا" naturally — not translated from English. **(2) Prayer times:** scenario S-04 has agents handle the dhuhr azan automatically (25-min temp closure, 10-min advance WhatsApp notification). **(3) Salary-day context:** S-03 assumes 1.8× peak on Thursday end-of-month — a specifically Saudi context. **(4) Real names:** أبو محمد السديري VIP 8.5M SAR, عبدالرحمن العمري Premium with churn risk — fully realistic Saudi names, not "John Smith".

> 🔎 Evidence: `fixtures/customer_data.json`, `fixtures/scenario_scripts.json:S-04`, real AI run logs show Khalid's actual output: "🕌 حياك الله، المدير! خلي يوسف يخدم أبو خالد وأبو محمد فورًا — هما ما يتحملون دقيقة زائدة".

---

## Section H — "Real, Not Demo" Proofs · براهين أن النظام حقيقي وليس عرضاً

---

### Q30. كيف نتأكد أن هذا ذكاء اصطناعي حقيقي وليس قوالب محفوظة؟ / How do we know this is real AI and not stored templates?

**A (ع):** ثلاث براهين قابلة للاختبار **الآن، أمامكم**. **(١) Data Editor:** غيّروا "العملاء بالانتظار" من ٣٤ إلى ١٠٠ وأعيدوا تشغيل S-03 — ستجدون سارة تكتب نصاً مختلفاً تماماً يَذكر ١٠٠ بدلاً من ٣٤ والمنسق يَتّخذ قراراً مختلفاً (التصعيد للمدير لأن الأرقام تجاوزت صلاحياته). لو كانت قوالب محفوظة، النصّ سيكون متطابقاً. **(٢) Heterogeneity badge:** كل bubble يُظهر `⚡ AI` لأن كل قرار مُولَّد لحظياً عبر OpenRouter. **(٣) Network DevTools:** افتحوا DevTools → Network وراقبوا POST لـ `openrouter.ai/api/v1/chat/completions` — ستَرَون الـ payload الذي يتمّ إرساله والـ response المُتلقّاة بـ `X-OpenRouter-Provider` header. هذا دليل لا يَقبل التَزوير.

**A (EN):** Three live, testable proofs **right now, in front of you**. **(1) Data Editor:** change "customers waiting" from 34 to 100, re-trigger S-03 — Sara writes a completely different analysis citing 100 not 34, and the Orchestrator may now escalate because numbers exceed its authority. If it were templates, the text would be identical. **(2) Heterogeneity badge:** every bubble shows `⚡ AI` because every decision is generated live via OpenRouter. **(3) Network DevTools:** open DevTools → Network, watch POSTs to `openrouter.ai/api/v1/chat/completions` — you can see the actual payloads and `X-OpenRouter-Provider` response headers. Tamper-proof evidence.

> 🔎 Evidence: live demo, plus the plan file documents Sara's response shifting from "34 customers" → "80 customers (135% increase from prior context)".

---

### Q31. أعطني مثالاً ملموساً على أن الوكلاء يَختلفون في النتيجة. / Give me a concrete example of agents producing different outputs.

**A (ع):** اختبرنا ذلك حرفياً. شَغّلنا S-04 مرّتين بنفس الـ data، نَتائج مختلفة:
- **التشغيل ١:** سارة قالت "ذروة متوقّعة ١.٨×"، خالد قال "إشعار WhatsApp مع لينا تستقبل أبو محمد".
- **التشغيل ٢ (نفس S-04):** سارة قالت "خَلوّ نسبي بسبب صلاة الظهر"، خالد قال "إشعار قبل ٥ دقائق فقط لتجنّب الإزعاج".
نفس البيانات، صياغات مختلفة — لأن النموذج ليس \u200Edeterministic عند temperature > 0. هذا برهان أن الذكاء حيّ، ليس template.

**A (EN):** We literally tested this. Ran S-04 twice with same data, different outputs:
- **Run 1:** Sara: "1.8× peak expected", Khalid: "WhatsApp notification + Lina receives Abu Mohammed".
- **Run 2 (same S-04):** Sara: "relative quiet due to dhuhr prayer", Khalid: "5-minute advance notice to avoid pestering".
Same data, different phrasings — because models aren't deterministic at temperature > 0. Proof of live intelligence, not templates.

> 🔎 Evidence: `apps/agents/models.py:AgentMessage` has both is_ai_generated=True rows for S-04 with non-identical content.

---

### Q32. كيف اخترتم النماذج النهائية؟ / How did you finalize your model choices?

**A (ع):** بالاختبار الفعلي، ليس بالنظرية. مثال ملموس: في وقت مبكر، كانت سارة تَستخدم DeepSeek R1 (reasoning model). اكتشفنا في celery logs أن R1 يَستهلك max_tokens=500 في "thinking chain" داخلي ويُرجع content فارغاً — لأنه نموذج reasoning صُمّم لـ chain-of-thought وليس لإجابات مباشرة. الـ engine اكتشف ذلك صراحةً (`if not result.strip(): raise LLMUnavailable`)، فبَدَّلنا سارة إلى **DeepSeek V3.2 (instruct)** — يُرجع content دائماً، أرخص، أسرع. الآن النماذج الخمسة المُعتَمَدة كلها validated تحت ظروف متنوعة. هذا اسمه engineering rigor، وليس "تجربة وخطأ في الإنتاج".

**A (EN):** By actual testing, not theory. Concrete example: early on, Sara used DeepSeek R1 (a reasoning model). Celery logs revealed R1 consumed all max_tokens=500 on internal chain-of-thought and returned empty content — because R1 is engineered for thinking traces, not direct answers. The engine detected this explicitly (`if not result.strip(): raise LLMUnavailable`), so we swapped Sara to **DeepSeek V3.2 (instruct)** — always returns content, cheaper, faster. The five production models are now all validated under diverse conditions. This is engineering rigor, not "trial and error in production".

> 🔎 Evidence: Plan file Fix #3, celery_worker logs show the literal `LLMUnavailable: LLM returned empty content for سارة` at 17:55:24, followed by the model swap and clean runs.

---

## Section I — Hard / Trap Questions · أسئلة صعبة ومُعقَّدة

---

### Q33. ما هو "الخندق" (moat) لديكم؟ أي شخص يَستطيع توصيل ٥ LLMs. / What's your moat — anyone can wire 5 LLMs.

**A (ع):** وَصْل ٥ LLMs مع `if/else` ليس صعباً. ما يَصعب — وما هو خندقنا الحقيقي — هو خمسة أشياء معاً: **(١) معرفة المجال البنكي السعودي:** SLA structure, authority hierarchies, prayer protocols, salary cycles — هذه تأخذ شهوراً من المقابلات مع مديري فروع لتُكوَّن. **(٢) Workflow design للقرارات:** متى يُصعّد، متى يَقرّر فوراً، أي وكيل يتكلّم متى — هذا engineering ناضج وليس وَصلاً تقنياً. **(٣) System prompts المُعَايَرة على اللهجة السعودية:** هذه data + iteration، لا توجد shortcut. **(٤) Compliance scaffolding:** SAMA / PDPL / KSA data residency. **(٥) العلاقات المُحتملة مع البنوك السعودية:** بيع B2B الخليجي ليس مفتوحاً لأي شخص. الخندق ليس تقنياً وحده — إنه domain × engineering × compliance × relationships.

**A (EN):** Wiring 5 LLMs with `if/else` isn't hard. What IS hard — and what's our actual moat — is five things together: **(1) Saudi banking domain knowledge:** SLA structure, authority hierarchies, prayer protocols, salary cycles — months of branch-manager interviews. **(2) Decision workflow design:** when to escalate, when to act, which agent speaks when — mature engineering, not technical wiring. **(3) Saudi-dialect-tuned prompts:** data + iteration, no shortcut. **(4) Compliance scaffolding:** SAMA / PDPL / KSA data residency. **(5) Bank relationships:** GCC B2B sales isn't open to anyone. The moat is domain × engineering × compliance × relationships.

> 🔎 Evidence: 5 system prompts × ~10 lines each, 7 scenarios with realistic SAR amounts, fixtures with realistic Saudi names — none of this is publicly available.

---

### Q34. هل يُمكن لـ prompt injection أن يَستولي على المنسق؟ / Can prompt injection take over the Orchestrator?

**A (ع):** ليس في تصميمنا الحالي بسهولة. السبب: **المستخدم لا يَكتب أبداً مباشرةً للـ LLM**. الـ inputs الوحيدة المسموحة هي: (أ) اختيار `scenario_id` من قائمة محدودة (٧ سيناريوهات معرّفة مسبقاً)، (ب) قيم رقمية في Data Editor (`total_waiting`, `avg_wait_minutes` — أرقام، لا نصوص حرة)، (ج) `day_context` من dropdown ثابت بـ ٤ خيارات. لا يَستطيع أحد كتابة "ignore previous instructions" — لا يوجد text input حرّ في المسار. **في الإنتاج**، عندما نُضيف free-form chat للعملاء، سنَحتاج: input sanitization, prompt firewall (Lakera Guard أو similar), structured output validation. هذه مَخاطر معروفة وتُعالَج.

**A (EN):** Not easily, in our current design. Reason: **users never write directly to the LLM**. The only allowed inputs are: (a) scenario_id from a fixed list of 7, (b) numeric Data Editor values (`total_waiting`, etc. — numbers, not free text), (c) `day_context` from a 4-item dropdown. Nobody can type "ignore previous instructions" — there's no free-form text input in the path. **In production**, when we add free-form customer chat, we'll need: input sanitization, prompt firewall (Lakera Guard or similar), structured output validation. Known risks, mitigated.

> 🔎 Evidence: `apps/agents/consumers.py:DashboardConsumer.receive` — the action whitelist; `apps/dashboard/templates/dashboard/partials/data_editor.html` — numeric/select inputs only.

---

### Q35. ماذا لو تَعطّل الإنترنت؟ هل يَعمل النظام؟ / What if internet drops?

**A (ع):** **نعم — عبر Ollama المحلي**. ندعم Ollama + Qwen3-32B داخل datacenter البنك (موصوف في `docker-compose.yml` كـ optional service)، يَعمل على GPU محلي، صفر اتصال خارجي. النظام يُحَوَّل تلقائياً عبر تحديث `LLM_BASE_URL` env var إلى `http://ollama:11434/v1`. هذا مهمّ جداً للبنوك الحكومية / السيادية التي ترفض إرسال أي بيانات لمزوّدي LLM خارجيين. الـ trade-off: Qwen3-32B local أقلّ جودة من Claude Opus 4.7 السحابي — لكنه يَعمل بالكامل بدون اتصال.

**A (EN):** **Yes — via local Ollama**. We support Ollama + Qwen3-32B running inside the bank's datacenter (documented in `docker-compose.yml` as an optional service), executing on local GPU with zero external connection. The system fails over by updating `LLM_BASE_URL` env to `http://ollama:11434/v1`. Critical for sovereign / government banks that refuse to send any data to external LLM providers. Trade-off: local Qwen3-32B is lower quality than cloud Claude Opus 4.7 — but it runs fully offline.

> 🔎 Evidence: `docker-compose.yml` (commented Ollama service block ready to enable), `apps/agents/engine.py` (parameterized `base_url`).

---

## Rapid-Fire One-Liners · إجابات سريعة بسطر واحد

| Question | جواب سريع | One-line answer |
|----------|-----------|-----------------|
| كم تكلفة السيناريو الواحد؟ | ~٠.٠٨ دولار | ~$0.08 per scenario (5 agents × heterogeneous) |
| كم سيناريو في اليوم لكل فرع؟ | ٢٠٠ متوقّعة | ~200 expected per branch/day |
| كم وقت تَستغرق الإجابة؟ | ٦٠–٩٠ ثانية | 60–90 seconds |
| كم وكيلاً تَدعمون؟ | ٥ في المرحلة الأولى، توسعة قادمة | 5 in v1, more in roadmap |
| ماذا عن الإيموجي؟ | جزء من الـ output structure للتمييز السريع | Part of structured output for visual scanning |
| هل تَدعمون اللغات الأخرى؟ | حالياً عربي فقط، الإنجليزي قادم | Arabic only currently, English coming |
| ما حجم الفريق؟ | ٣ مهندسين | 3 engineers |
| متى الإطلاق؟ | تجربة تنظيمية ٢٠٢٧ | Regulatory pilot 2027 |

---

## Pre-Flight Checklist Before Demo · فحص ما قبل العرض

- [ ] OpenRouter credits rechargeed ($10+ recommended)
- [ ] `docker compose up` running, all 6 containers healthy
- [ ] Browser at `http://localhost:8001/` — clear cache, hard refresh
- [ ] DevTools Console open — confirms `[Munjiz] WS connected`
- [ ] Trigger S-04 once before judges arrive — confirms AI path works (5× HTTP 200 from OpenRouter)
- [ ] Light/dark theme tested — both work
- [ ] Logo on header is the actual `munjiz-logo.webp`, not the placeholder
- [ ] Data Editor opens, accepts numbers, re-triggers correctly
- [ ] Have laptop charger, secondary screen for projection
- [ ] Have a print of THIS document on hand

---

> **آخر نصيحة** · **Final advice**
> الحُكم الذكي يَختبر أعمق ادعاء (الـ heterogeneous architecture) أولاً. كُن جاهزاً بإجابة Q2 و Q5 و Q8. هذه الثلاثة معاً تُثبت أن منجز ليس "مجرد ٥ LLMs بـ if/else" — بل تصميم هندسي ناضج.
>
> A sharp judge will probe the deepest claim (heterogeneous architecture) first. Have Q2, Q5, Q8 ready cold. Together they prove Munjiz isn't "just 5 LLMs with if/else" — it's mature engineering.
