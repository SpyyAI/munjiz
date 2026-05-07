// Flash effect on KPI value when it changes.
// Watches all .counter-value spans and adds a brief flash class on text mutation.

(function () {
    function watchCounters() {
        const observer = new MutationObserver((mutations) => {
            for (const m of mutations) {
                if (m.type === 'characterData' || m.type === 'childList') {
                    const el = m.target.parentElement?.classList?.contains('counter-value')
                        ? m.target.parentElement
                        : null;
                    if (el) {
                        el.classList.add('flash');
                        setTimeout(() => el.classList.remove('flash'), 350);
                    }
                }
            }
        });
        // Re-attach periodically as Alpine re-renders
        setInterval(() => {
            document.querySelectorAll('.counter-value').forEach((el) => {
                if (!el._munjizObserved) {
                    observer.observe(el, { childList: true, characterData: true, subtree: true });
                    el._munjizObserved = true;
                }
            });
        }, 1000);
    }

    if (document.readyState === 'complete') watchCounters();
    else window.addEventListener('load', watchCounters);
})();
