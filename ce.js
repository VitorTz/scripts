// ==UserScript==
// @name         F2 Automation & CEP Viewer
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Press F2 to simulate Enter, Copy, Backspace, and F7 with delays. Displays CEP input value on the bottom left.
// @author       You
// @match        *://*/*
// @grant        GM_setClipboard
// ==/UserScript==

(function() {
    'use strict';

    // Delay between each action in milliseconds
    const DELAY_MS = 150;

    // Helper function to create a delay
    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    // Helper function to dispatch keyboard events
    const dispatchKey = (target, eventType, key, code, keyCode) => {
        const event = new KeyboardEvent(eventType, {
            key: key,
            code: code,
            keyCode: keyCode,
            which: keyCode,
            bubbles: true,
            cancelable: true
        });
        target.dispatchEvent(event);
    };

    // Main sequence execution
    const executeF2Sequence = async () => {
        const activeEl = document.activeElement || document.body;

        // 1. Enter
        dispatchKey(activeEl, 'keydown', 'Enter', 'Enter', 13);
        dispatchKey(activeEl, 'keyup', 'Enter', 'Enter', 13);
        await sleep(DELAY_MS);

        // 2. Copy to clipboard
        let textToCopy = '';
        if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA') {
            textToCopy = activeEl.value;
        } else {
            textToCopy = window.getSelection().toString();
        }
        
        if (textToCopy) {
            GM_setClipboard(textToCopy, 'text');
        }
        await sleep(DELAY_MS);

        // 3. Backspace
        dispatchKey(activeEl, 'keydown', 'Backspace', 'Backspace', 8);
        
        // Natively remove the last character if it is a text field
        if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA') {
            activeEl.value = activeEl.value.slice(0, -1);
            // Dispatch input event so frontend frameworks (React, Angular) detect the change
            activeEl.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        dispatchKey(activeEl, 'keyup', 'Backspace', 'Backspace', 8);
        await sleep(DELAY_MS);

        // 4. F7
        dispatchKey(activeEl, 'keydown', 'F7', 'F7', 118);
        dispatchKey(activeEl, 'keyup', 'F7', 'F7', 118);
    };

    // Listen for the F2 key press
    window.addEventListener('keydown', async (e) => {
        if (e.key === 'F2') {
            e.preventDefault(); // Prevent default browser F2 behavior
            await executeF2Sequence();
        }
    });

    // Create the visual UI for the CEP value
    const cepDisplay = document.createElement('div');
    Object.assign(cepDisplay.style, {
        position: 'fixed',
        bottom: '15px',
        left: '15px',
        padding: '10px 15px',
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        color: '#4CAF50',
        fontFamily: 'monospace',
        fontSize: '16px',
        fontWeight: 'bold',
        borderRadius: '8px',
        zIndex: '999999',
        pointerEvents: 'none',
        boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
    });
    cepDisplay.textContent = 'CEP: Aguardando...';
    document.body.appendChild(cepDisplay);

    // Function to search for the CEP input and update the UI
    const updateCepDisplay = () => {
        // Query inputs where the title attribute contains 'cep' (case-insensitive)
        const cepInput = document.querySelector('input[title*="cep" i]');
        if (cepInput) {
            cepDisplay.textContent = `CEP: ${cepInput.value || 'Vazio'}`;
        }
    };

    // Listen for typing on the page to update the UI instantly
    document.addEventListener('input', (e) => {
        if (e.target && e.target.tagName === 'INPUT') {
            const title = e.target.getAttribute('title') || '';
            if (title.toLowerCase().includes('cep')) {
                cepDisplay.textContent = `CEP: ${e.target.value || 'Vazio'}`;
            }
        }
    });

    // Periodic check in case the CEP is filled automatically by an API or another script
    setInterval(updateCepDisplay, 1000);

})();
