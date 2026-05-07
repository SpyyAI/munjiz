// Munjiz Dashboard — Alpine.js component
// Listens to MunjizBus, manages messages/agent statuses/KPIs/data editor.

// ============== Theme toggle ==============
(function(){
    const root = document.documentElement;
    const btn = document.getElementById('themeToggle');
    function syncLogos() {
        const t = root.getAttribute('data-theme') || 'dark';
        const want = t === 'light' ? '/static/munjiz-logo-clean.png' : '/static/munjiz-logo.webp';
        document.querySelectorAll('img[data-logo]').forEach(img => { img.src = want; });
    }
    syncLogos();
    if (btn) {
        btn.addEventListener('click', () => {
            const cur = root.getAttribute('data-theme') || 'dark';
            const nxt = cur === 'dark' ? 'light' : 'dark';
            root.setAttribute('data-theme', nxt);
            try { localStorage.setItem('munjiz-theme', nxt); } catch(e){}
            syncLogos();
        });
    }
})();

const MUNJIZ_DEBUG = true;
function mlog(...args) { if (MUNJIZ_DEBUG) console.log('[Munjiz]', ...args); }
mlog('dashboard.js loaded at', new Date().toISOString());

function munjizDashboard() {
    return {
        wsConnected: false,
        currentTime: '',
        messages: [],
        typingAgent: null,
        agentStatuses: {},
        kpis: [],
        activeScenario: null,
        isPlaying: false,
        lastFlow: null,
        playbackTimer: null,

        dataEditorOpen: false,
        customData: {
            scenario_id: 'S-03',
            queue_state: { total_waiting: 34, avg_wait_minutes: 18, sla_compliance: 78 },
            day_context: 'خميس — نهاية الشهر — يوم رواتب',
        },

        init() {
            // Idempotency guard: never register bus listeners twice if Alpine re-mounts
            if (this._initDone) { mlog('init() skipped — already initialized'); return; }
            this._initDone = true;
            this.tickClock();
            setInterval(() => this.tickClock(), 1000);

            this.fetchKPIs();
            setInterval(() => this.fetchKPIs(), 5000);

            const bus = window.MunjizBus;
            bus.addEventListener('ws:open',  () => { this.wsConnected = true; mlog('WS connected'); });
            bus.addEventListener('ws:close', () => { this.wsConnected = false; mlog('WS closed'); });

            bus.addEventListener('agent:message', (e) => this.handleIncomingMessage(e.detail));
            bus.addEventListener('agent:status',  (e) => this.handleStatusUpdate(e.detail));
            bus.addEventListener('metrics:update',(e) => this.handleMetricsUpdate(e.detail));
            bus.addEventListener('scenario:started', (e) => this.handleScenarioStarted(e.detail));
            bus.addEventListener('scenario:ended',   (e) => this.handleScenarioEnded(e.detail));
            mlog('Alpine init complete; bus listeners attached');
        },

        tickClock() {
            const d = new Date();
            this.currentTime = d.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
        },

        async fetchKPIs() {
            try {
                const r = await fetch('/api/analytics/today/');
                const data = await r.json();
                this.kpis = data.kpis || [];
            } catch (e) { /* silent */ }
        },

        triggerScenario(scenarioId) {
            if (this.isPlaying) return;
            this.activeScenario = scenarioId;
            this.isPlaying = true;
            this.messages = [];
            this.typingAgent = null;
            const list = document.getElementById('feed-messages');
            if (list) list.innerHTML = '';
            const empty = document.getElementById('feed-empty');
            if (empty) empty.style.display = 'none';
            window.MunjizSend({ action: 'trigger_scenario', scenario_id: scenarioId });

            // Safety: release isPlaying lock after 60s in case nothing arrives
            clearTimeout(this.playbackTimer);
            this.playbackTimer = setTimeout(() => { this.isPlaying = false; }, 60000);
        },

        triggerWithCustomData() {
            if (this.isPlaying) return;
            this.activeScenario = this.customData.scenario_id;
            this.isPlaying = true;
            this.messages = [];
            this.typingAgent = null;
            const list = document.getElementById('feed-messages');
            if (list) list.innerHTML = '';
            const empty = document.getElementById('feed-empty');
            if (empty) empty.style.display = 'none';
            window.MunjizSend({
                action: 'update_data',
                scenario_id: this.customData.scenario_id,
                custom_data: {
                    queue_state: this.customData.queue_state,
                    day_context: this.customData.day_context,
                },
            });
            clearTimeout(this.playbackTimer);
            this.playbackTimer = setTimeout(() => { this.isPlaying = false; }, 60000);
        },

        handleIncomingMessage(msg) {
            mlog('msg received:', msg.from_agent, '→', (msg.content || '').slice(0, 60));
            // Dedupe: skip if we've already rendered a bubble with this id
            if (msg.id && document.querySelector(`[data-msg-id="${msg.id}"]`)) {
                mlog('skipped duplicate id', msg.id);
                return;
            }
            // Direct DOM manipulation — bypasses Alpine reactivity issues with x-for + dynamic includes
            this._showTyping(msg.from_name, msg.from_color);

            setTimeout(() => {
                this._hideTyping();
                this._appendMessageBubble(msg);
                this.scrollFeedToBottom();

                if (window.MunjizPulseEdge) window.MunjizPulseEdge(msg.from_agent);
                this.lastFlow = `${msg.from_name} → المنسق`;

                if (msg.from_agent === 'orchestrator') {
                    setTimeout(() => { this.isPlaying = false; }, 600);
                }
            }, 700);
        },

        _showTyping(name, color) {
            const empty = document.getElementById('feed-empty');
            if (empty) empty.style.display = 'none';
            const t = document.getElementById('feed-typing');
            if (!t) return;
            t.className = 'bg-munjiz-bg/40 rounded-lg p-4 flex items-center gap-3 animate-pulse';
            t.style.borderRight = `4px solid ${color}`;
            t.innerHTML = `
                <div class="w-7 h-7 rounded-full flex items-center justify-center font-bold text-white text-xs"
                     style="background:${color};">${(name || '').charAt(0)}</div>
                <span class="text-xs text-munjiz-muted">${name} يكتب...</span>
                <div class="flex gap-1 mr-auto">
                    <span class="w-2 h-2 rounded-full bouncing-dot" style="background:${color};"></span>
                    <span class="w-2 h-2 rounded-full bouncing-dot" style="background:${color}; animation-delay: 0.15s;"></span>
                    <span class="w-2 h-2 rounded-full bouncing-dot" style="background:${color}; animation-delay: 0.3s;"></span>
                </div>`;
        },

        _hideTyping() {
            const t = document.getElementById('feed-typing');
            if (t) { t.className = 'hidden'; t.innerHTML = ''; }
        },

        _appendMessageBubble(msg) {
            const list = document.getElementById('feed-messages');
            if (!list) return;
            const bubble = document.createElement('div');
            bubble.className = 'message-bubble bg-munjiz-bg/60 rounded-lg p-4 transition-all';
            bubble.style.borderRight = `4px solid ${msg.from_color}`;
            if (msg.id) bubble.setAttribute('data-msg-id', msg.id);
            const time = this.formatTime(msg.timestamp);
            const typeLabel = this.msgTypeLabel(msg.message_type);
            // Source badge: AI-generated vs scripted fallback
            const isAI = msg.is_ai_generated === true;
            const sourceBadge = isAI
                ? '<span class="text-[9px] px-1.5 py-0.5 rounded font-bold bg-agent-orchestrator/20 text-agent-orchestrator">⚡ AI</span>'
                : '<span class="text-[9px] px-1.5 py-0.5 rounded font-bold bg-munjiz-muted/20 text-munjiz-muted">📜 سيناريو</span>';
            bubble.innerHTML = `
                <div class="flex items-center gap-2 mb-2">
                    <div class="w-7 h-7 rounded-full flex items-center justify-center font-bold text-white text-xs"
                         style="background:${msg.from_color};">${(msg.from_name || '').charAt(0)}</div>
                    <span class="font-bold text-sm"></span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wide"
                          style="background:${msg.from_color}33; color:${msg.from_color};"></span>
                    ${sourceBadge}
                    <span class="text-[10px] text-munjiz-muted mr-auto"></span>
                </div>
                <p class="text-sm leading-relaxed whitespace-pre-wrap"></p>`;
            // Set text content safely (no XSS via innerHTML) — only spans without inline content
            const spans = bubble.querySelectorAll('div.flex > span');
            spans[0].textContent = msg.from_name || '';
            spans[1].textContent = typeLabel;
            spans[3].textContent = time;
            bubble.querySelector('p').textContent = msg.content || '';
            list.appendChild(bubble);
            mlog('bubble appended #', list.children.length, 'visible=', list.offsetHeight > 0);
        },

        handleScenarioStarted(data) {
            mlog('scenario_started', data.scenario_id, 'mode=', data.mode);
            // Reset DOM in EVERY connected tab so 2-tab + reclick scenarios stay clean
            this.activeScenario = data.scenario_id;
            this.isPlaying = true;
            const list = document.getElementById('feed-messages');
            if (list) list.innerHTML = '';
            this._hideTyping();
            const empty = document.getElementById('feed-empty');
            if (empty) empty.style.display = 'none';
        },

        handleScenarioEnded(data) {
            mlog('scenario_ended', data.scenario_id, 'mode=', data.mode);
            this.isPlaying = false;
        },

        handleStatusUpdate(data) {
            this.agentStatuses[data.agent_type] = {
                status: data.status,
                current_task: data.current_task,
            };
            // Apply 'thinking' class on the SVG node for glow effect
            const node = document.querySelector(`#agent-network-svg [data-agent="${data.agent_type}"]`);
            if (node) {
                node.classList.toggle('thinking', data.status === 'thinking');
            }
        },

        handleMetricsUpdate(data) {
            // Will be used for live pushed metrics; for now we poll /api/analytics/today/
        },

        clearFeed() {
            this.messages = [];
            this.typingAgent = null;
            this.activeScenario = null;
            this.isPlaying = false;
            const list = document.getElementById('feed-messages');
            if (list) list.innerHTML = '';
            this._hideTyping();
            const empty = document.getElementById('feed-empty');
            if (empty) empty.style.display = '';
        },

        scrollFeedToBottom() {
            const feed = document.getElementById('message-feed');
            if (feed) {
                requestAnimationFrame(() => { feed.scrollTop = feed.scrollHeight; });
            }
        },

        formatTime(iso) {
            try {
                return new Date(iso).toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit', hour12: false });
            } catch { return ''; }
        },

        msgTypeLabel(t) {
            return ({
                alert: 'تنبيه', analysis: 'تحليل', suggestion: 'اقتراح',
                decision: 'قرار', update: 'تحديث', question: 'سؤال', confirmation: 'تأكيد',
            })[t] || t;
        },
    };
}
