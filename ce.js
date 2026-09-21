// ==UserScript==
// @name         Customizable Macro & CEP Viewer
// @namespace    http://tampermonkey.net/
// @version      1.2
// @description  Customizable trigger key to simulate Enter, Copy, Backspace, and F7. Displays CEP input value.
// @author       You
// @match        *://*/*
// @grant        GM_setClipboard
// @grant        GM_setValue
// @grant        GM_getValue
// ==/UserScript==

(function() {
    'use strict';

    // Delay between each action in milliseconds
    const DELAY_MS = 150;
    
    // Load saved trigger key from Tampermonkey storage, default to 'Space'
    let triggerKeyCode = GM_getValue('macroTriggerKey', 'Space');
    let isRecordingKey = false;

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
    const executeSequence = async () => {
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
            // Dispatch input event so frontend frameworks detect the change
            activeEl.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        dispatchKey(activeEl, 'keyup', 'Backspace', 'Backspace', 8);
        await sleep(DELAY_MS);

        // 4. F7
        dispatchKey(activeEl, 'keydown', 'F7', 'F7', 118);
        dispatchKey(activeEl, 'keyup', 'F7', 'F7', 118);
    };

    // Main Keyboard Listener
    window.addEventListener('keydown', async (e) => {
        // If the user clicked the button to change the key
        if (isRecordingKey) {
            e.preventDefault();
            e.stopPropagation();
            
            triggerKeyCode = e.code;
            GM_setValue('macroTriggerKey', triggerKeyCode); // Save for future sessions
            
            keyButton.textContent = `Trigger: [ ${triggerKeyCode} ]`;
            keyButton.style.backgroundColor = '#4CAF50';
            isRecordingKey = false;
            return;
        }

        // If the pressed key matches our trigger key
        if (e.code === triggerKeyCode) {
            // Only prevent default if we are not typing in an input (unless it's the specific behavior you want)
            // Uncomment the next line if you want to completely block the trigger key from typing naturally
            // e.preventDefault(); 
            
            await executeSequence();
        }
    });

    // --- UI Creation ---

    // Main container
    const uiContainer = document.createElement('div');
    Object.assign(uiContainer.style, {
        position: 'fixed',
        bottom: '15px',
        left: '15px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        zIndex: '999999'
    });

    // Config Button
    const keyButton = document.createElement('button');
    Object.assign(keyButton.style, {
        padding: '8px 12px',
        backgroundColor: '#4CAF50',
        color: '#fff',
        border: 'none',
        borderRadius: '6px',
        fontFamily: 'monospace',
        fontSize: '14px',
        fontWeight: 'bold',
        cursor: 'pointer',
        boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
        transition: 'background-color 0.2s'
    });
    keyButton.textContent = `Trigger: [ ${triggerKeyCode} ]`;
    
    keyButton.addEventListener('click', () => {
        isRecordingKey = true;
        keyButton.textContent = 'Press any key...';
        keyButton.style.backgroundColor = '#ff9800'; // Orange to indicate recording state
    });

    // CEP Display
    const cepDisplay = document.createElement('div');
    Object.assign(cepDisplay.style, {
        padding: '10px 15px',
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        color: '#4CAF50',
        fontFamily: 'monospace',
        fontSize: '16px',
        fontWeight: 'bold',
        borderRadius: '6px',
        pointerEvents: 'none',
        boxShadow: '0 4px 6px rgba(0,0,0,0.3)'
    });
    cepDisplay.textContent = 'CEP: Waiting...';

    // Assemble UI
    uiContainer.appendChild(keyButton);
    uiContainer.appendChild(cepDisplay);
    document.body.appendChild(uiContainer);

    // --- CEP Observer Logic ---

    // Function to search for the CEP input and update the UI
    const updateCepDisplay = () => {
        // Query inputs where the title attribute contains 'cep' (case-insensitive)
        const cepInput = document.querySelector('input[title*="cep" i]');
        if (cepInput) {
            cepDisplay.textContent = `CEP: ${cepInput.value || 'Empty'}`;
        }
    };

    // Listen for typing on the page to update the UI instantly
    document.addEventListener('input', (e) => {
        if (e.target && e.target.tagName === 'INPUT') {
            const title = e.target.getAttribute('title') || '';
            if (title.toLowerCase().includes('cep')) {
                cepDisplay.textContent = `CEP: ${e.target.value || 'Empty'}`;
            }
        }
    });

    // Periodic check in case the CEP is filled automatically by an API or another script
    setInterval(updateCepDisplay, 1000);

})();
