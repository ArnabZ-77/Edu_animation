document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const promptInput = document.getElementById('promptInput');
    const generateBtn = document.getElementById('generateBtn');
    const statusCard = document.getElementById('statusCard');
    const statusBadge = document.getElementById('statusBadge');
    const progressBar = document.getElementById('progressBar');
    const terminalLogs = document.getElementById('terminalLogs');
    
    const videoPlaceholder = document.getElementById('videoPlaceholder');
    const videoPlayer = document.getElementById('videoPlayer');
    const videoSource = document.getElementById('videoSource');
    const sceneNameLabel = document.getElementById('sceneNameLabel');
    
    const codeDisplay = document.getElementById('codeDisplay');
    const copyCodeBtn = document.getElementById('copyCodeBtn');
    const historyList = document.getElementById('historyList');

    // Local state
    let history = JSON.parse(localStorage.getItem('animation_history')) || [];
    let progressTimer = null;

    // Load History list on startup
    renderHistory();

    // Copy code logic
    copyCodeBtn.addEventListener('click', () => {
        const codeText = codeDisplay.textContent;
        navigator.clipboard.writeText(codeText).then(() => {
            const icon = copyCodeBtn.querySelector('i');
            icon.className = 'fa-solid fa-check';
            icon.style.color = '#10b981';
            setTimeout(() => {
                icon.className = 'fa-regular fa-copy';
                icon.style.color = '';
            }, 2000);
        });
    });

    // Handle Generation Action
    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        // Reset UI States
        generateBtn.disabled = true;
        statusCard.classList.remove('hidden');
        statusBadge.className = 'status-badge processing';
        statusBadge.textContent = 'Processing';
        terminalLogs.innerHTML = '';
        progressBar.style.width = '0%';

        logConsole("Handshake established with local Flask server.", "info");
        logConsole(`Input Prompt: "${prompt}"`, "muted");

        // Start progressive mock log timeline
        startProgressTimeline();

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: prompt })
            });

            const result = await response.json();
            clearInterval(progressTimer);
            progressBar.style.width = '100%';

            if (response.ok && result.success) {
                // Success path
                statusBadge.className = 'status-badge success';
                statusBadge.textContent = 'Success';
                logConsole("Manim compiled animation successfully!", "success");
                logConsole(`Scene Class Name: ${result.class_name}`, "info");
                logConsole(`Video Ready at: ${result.video_url}`, "muted");

                // Update Player
                loadVideo(result.video_url, result.class_name);

                // Update Code Display
                codeDisplay.textContent = result.code;

                // Add to History
                const historyItem = {
                    prompt: prompt,
                    class_name: result.class_name,
                    video_url: result.video_url,
                    code: result.code,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                };
                
                history.unshift(historyItem);
                localStorage.setItem('animation_history', JSON.stringify(history));
                renderHistory();
            } else {
                // Compile / API Error path
                statusBadge.className = 'status-badge error';
                statusBadge.textContent = 'Error';
                logConsole(`Error: ${result.error || 'Server error occurred'}`, "err");
                if (result.details) {
                    logConsole(`Details:\n${result.details}`, "err");
                }
            }
        } catch (error) {
            clearInterval(progressTimer);
            progressBar.style.width = '100%';
            statusBadge.className = 'status-badge error';
            statusBadge.textContent = 'Failed';
            logConsole(`Pipeline connection failed: ${error.message}`, "err");
        } finally {
            generateBtn.disabled = false;
        }
    });

    // Helper functions
    function logConsole(message, type = 'info') {
        const line = document.createElement('div');
        line.className = `log-line text-${type}`;
        
        let icon = '';
        if (type === 'info') icon = '<i class="fa-solid fa-circle-info"></i> ';
        if (type === 'success') icon = '<i class="fa-solid fa-circle-check"></i> ';
        if (type === 'err') icon = '<i class="fa-solid fa-triangle-exclamation"></i> ';
        if (type === 'warn') icon = '<i class="fa-solid fa-circle-exclamation"></i> ';
        
        line.innerHTML = `${icon}${escapeHtml(message)}`;
        terminalLogs.appendChild(line);
        terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function loadVideo(url, className) {
        videoPlaceholder.classList.add('hidden');
        videoPlayer.classList.remove('hidden');
        videoSource.src = url;
        videoPlayer.load();
        videoPlayer.play();
        sceneNameLabel.textContent = className;
    }

    function startProgressTimeline() {
        let elapsed = 0;
        const timeline = [
            { t: 0, p: 10, msg: "Contacting Gemini API for code blueprint...", type: "info" },
            { t: 3, p: 25, msg: "Gemini response received. Cleaning markup headers...", type: "info" },
            { t: 5, p: 40, msg: "Scene structure extracted. Generating 'generated_scene.py' file...", type: "info" },
            { t: 8, p: 55, msg: "Initiating Manim CLI compiler on sub-process...", type: "info" },
            { t: 12, p: 70, msg: "Rendering camera viewport meshes & vector coordinates...", type: "info" },
            { t: 16, p: 85, msg: "Merging partial MP4 renders into main composition...", type: "info" },
            { t: 22, p: 95, msg: "Waiting for final compilation write lock to release...", type: "warn" }
        ];

        progressTimer = setInterval(() => {
            elapsed += 0.5;
            const currentItem = timeline.find(item => item.t === elapsed);
            if (currentItem) {
                progressBar.style.width = `${currentItem.p}%`;
                logConsole(currentItem.msg, currentItem.type);
            }
        }, 500);
    }

    function renderHistory() {
        if (history.length === 0) {
            historyList.innerHTML = '<li class="empty-history-text">No animations generated yet.</li>';
            return;
        }

        historyList.innerHTML = '';
        history.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = 'history-item';
            li.innerHTML = `
                <span class="item-prompt">${escapeHtml(item.prompt)}</span>
                <span class="item-time"><i class="fa-regular fa-clock"></i> ${item.timestamp} | ${item.class_name}</span>
            `;
            
            li.addEventListener('click', () => {
                // Clear active states
                document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
                li.classList.add('active');

                // Load cached scene in UI
                loadVideo(item.video_url, item.class_name);
                codeDisplay.textContent = item.code;
                
                // Show status
                statusCard.classList.remove('hidden');
                statusBadge.className = 'status-badge success';
                statusBadge.textContent = 'Loaded';
                terminalLogs.innerHTML = '';
                progressBar.style.width = '100%';
                logConsole(`Loaded animation from local history: ${item.class_name}`, "success");
            });

            historyList.appendChild(li);
        });
    }
});
