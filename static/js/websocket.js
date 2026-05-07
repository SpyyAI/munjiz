// Munjiz WebSocket client — connects to /ws/dashboard/ and dispatches events.
// All events are forwarded to a global window.MunjizBus that Alpine listens to.

(function () {
    // Idempotency guard: if this script gets injected twice (cache + reload weirdness), skip the second run
    if (window.__munjizWSInit) {
        console.warn('Munjiz WS already initialized — skipping duplicate init');
        return;
    }
    window.__munjizWSInit = true;

    const bus = new EventTarget();
    window.MunjizBus = bus;

    let ws = null;
    let reconnectTimer = null;
    const seenMessageIds = new Set();  // dedupe at dispatch — never re-fire the same id

    function cleanupOldWs() {
        if (ws) {
            try {
                ws.onopen = ws.onclose = ws.onerror = ws.onmessage = null;
                if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
                    ws.close();
                }
            } catch (_) {}
        }
    }

    function connect() {
        cleanupOldWs();
        const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const url = `${proto}://${window.location.host}/ws/dashboard/`;
        ws = new WebSocket(url);

        ws.addEventListener('open', () => {
            console.log('🟢 Munjiz WS connected');
            bus.dispatchEvent(new CustomEvent('ws:open'));
        });

        ws.addEventListener('close', () => {
            console.log('🔴 Munjiz WS closed — reconnecting in 3s');
            bus.dispatchEvent(new CustomEvent('ws:close'));
            clearTimeout(reconnectTimer);
            reconnectTimer = setTimeout(connect, 3000);
        });

        ws.addEventListener('error', (e) => console.error('Munjiz WS error', e));

        ws.addEventListener('message', (event) => {
            let data;
            try { data = JSON.parse(event.data); } catch { return; }

            if (data.type === 'status_update') {
                bus.dispatchEvent(new CustomEvent('agent:status', { detail: data }));
            } else if (data.type === 'metrics_update') {
                bus.dispatchEvent(new CustomEvent('metrics:update', { detail: data }));
            } else if (data.type === 'scenario_started') {
                bus.dispatchEvent(new CustomEvent('scenario:started', { detail: data }));
            } else if (data.type === 'scenario_ended') {
                bus.dispatchEvent(new CustomEvent('scenario:ended', { detail: data }));
            } else if (data.type === 'hello' || data.type === 'pong' || data.type === 'ack') {
                // benign
            } else if (data.from_agent) {
                // Bus-level dedupe: if we've already dispatched this message id, drop the dup
                if (data.id && seenMessageIds.has(data.id)) {
                    console.log('Munjiz dropped duplicate WS frame for', data.id);
                    return;
                }
                if (data.id) seenMessageIds.add(data.id);
                bus.dispatchEvent(new CustomEvent('agent:message', { detail: data }));
            }
        });
    }

    window.MunjizSend = function (payload) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(payload));
            return true;
        }
        console.warn('Munjiz WS not ready, dropping payload', payload);
        return false;
    };

    connect();
})();
