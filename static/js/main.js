document.addEventListener('DOMContentLoaded', () => {

    // --- A simpler, more robust listener function ---
    function setupInputListener(inputId, targetWordId, onCompleteCallback) {
        const input = document.getElementById(inputId);
        const targetWordElement = document.getElementById(targetWordId);
        
        if (!input || !targetWordElement) {
            console.error(`Initialization failed: Could not find elements with IDs '${inputId}' or '${targetWordId}'`);
            return;
        }

        const targetWord = targetWordElement.innerText.trim();
        let events = [];
        
        const resetState = () => { events = []; };

        const handleKeyDown = (e) => {
            if (e.key.length !== 1 || e.ctrlKey || e.metaKey || e.altKey) return;
            if (input.value.length >= targetWord.length) {
                input.value = '';
                resetState();
            }
            events.push({ key: e.key, event: 'press', timestamp: performance.now() });
        };
        
        const handleKeyUp = (e) => {
            if (e.key.length !== 1 || e.ctrlKey || e.metaKey || e.altKey) return;
            events.push({ key: e.key, event: 'release', timestamp: performance.now() });

            if (input.value.toLowerCase() === targetWord.toLowerCase()) {
                if (events.length === targetWord.length * 2) {
                    onCompleteCallback(Array.from(events), targetWord); 
                } else {
                    console.warn(`Event count mismatch for word '${targetWord}'. Expected ${targetWord.length * 2}, but got ${events.length}. Resetting.`);
                }
                resetState();
            }
        };
        
        input.addEventListener('keydown', handleKeyDown);
        input.addEventListener('keyup', handleKeyUp);
        // This handles pastes or deletes, forcing a reset.
        input.addEventListener('input', (e) => {
            if (input.value.length === 0) {
                resetState();
            }
        });
    }

    // --- Live Prediction Logic ---
    async function handleLivePrediction(events, targetWord) {
        const resultDiv = document.getElementById('live-result');
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `<p class="info"><span class="spinner"></span>Processing...</p>`;

        try {
            const response = await fetch('/predict_live', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ events, target_word: targetWord })
            });
            const data = await response.json();

            if (!response.ok) {
                resultDiv.innerHTML = `<p class="error"><strong>Error:</strong> ${data.detail || 'Prediction failed.'}</p>`;
            } else {
                const formattedStyle = data.predicted_style.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                resultDiv.innerHTML = `
                    <p><strong>Predicted Style:</strong> <span class="success">${formattedStyle}</span></p>
                    <p><strong>Model Confidence:</strong> ${data.confidence.toFixed(2)}%</p>
                `;
            }
        } catch (err) {
            resultDiv.innerHTML = `<p class="error"><strong>Error:</strong> Could not connect to the server. Please check the terminal for errors.</p>`;
        }
    }

    // --- Data Submission Logic ---
    let lastValidSubmission = { events: [], targetWord: '' };
    window.submitTypingData = async () => {
        const styleSelect = document.getElementById('style-select');
        const selectedStyle = styleSelect.value;
        const resultDiv = document.getElementById('submit-result');
        const submitBtn = document.getElementById('submit-btn');

        if (!selectedStyle) {
            alert("Please select a typing style from the dropdown menu.");
            return;
        }
        if (lastValidSubmission.events.length === 0) {
            alert("A valid sample has not been typed in the submission box yet. Please type the word correctly.");
            return;
        }

        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `<p class="info"><span class="spinner"></span>Submitting...</p>`;
        submitBtn.disabled = true;

        try {
            const response = await fetch('/submit_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    style_id: selectedStyle,
                    events: lastValidSubmission.events,
                    target_word: lastValidSubmission.targetWord
                })
            });
            const data = await response.json();

            if (!response.ok) {
                resultDiv.innerHTML = `<p class="error"><strong>Error:</strong> ${data.detail || 'Submission failed.'}</p>`;
            } else {
                resultDiv.innerHTML = `<p class="success">${data.message}</p>`;
            }
        } catch (err) {
            resultDiv.innerHTML = `<p class="error"><strong>Error:</strong> Could not connect to the server.</p>`;
        } finally {
            submitBtn.disabled = false;
            lastValidSubmission = { events: [], targetWord: '' }; 
            document.getElementById('submit-input').value = '';
        }
    };

    // --- Initialize All Listeners ---
    setupInputListener('live-input', 'target-word-live', handleLivePrediction);
    
    setupInputListener('submit-input', 'target-word-submit', (events, targetWord) => {
        lastValidSubmission = { events, targetWord };
        const resultDiv = document.getElementById('submit-result');
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `<p class="info">Typing sample captured. Ready to submit.</p>`;
    });
});

