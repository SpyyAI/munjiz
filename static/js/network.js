// Pulse the SVG edge from agent → orchestrator when a message arrives.

window.MunjizPulseEdge = function (agentType) {
    const edge = document.querySelector(`#agent-network-svg line[data-from="${agentType}"]`);
    if (!edge) return;
    edge.classList.remove('edge-pulse');
    void edge.getBoundingClientRect();  // force reflow
    edge.classList.add('edge-pulse');
    edge.setAttribute('opacity', '0.9');
    setTimeout(() => edge.setAttribute('opacity', '0.2'), 800);
};
