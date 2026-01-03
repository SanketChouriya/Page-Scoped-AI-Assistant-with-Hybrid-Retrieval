const API_BASE = "http://localhost:8005";

const elements = {
    status: document.getElementById("status"),
    statusText: document.getElementById("status-text"),
    question: document.getElementById("question"),
    askBtn: document.getElementById("ask"),
    answerContainer: document.getElementById("answer-container"),
    answer: document.getElementById("answer"),
    metrics: document.getElementById("metrics"),
    metricSections: document.getElementById("metric-sections"),
    metricTokens: document.getElementById("metric-tokens"),
    metricTime: document.getElementById("metric-time")
};

function setStatus(type, message) {
    elements.status.className = `status ${type}`;
    elements.statusText.textContent = message;
}

function setLoading(loading) {
    elements.askBtn.disabled = loading;
    elements.askBtn.textContent = loading ? "Processing..." : "Ask Question";
}

function showAnswer(text, metrics = null) {
    elements.answerContainer.classList.remove("hidden");
    elements.answer.textContent = text;

    if (metrics) {
        elements.metrics.classList.remove("hidden");
        elements.metricSections.textContent = metrics.sections || "-";
        elements.metricTokens.textContent = metrics.tokens || "-";
        elements.metricTime.textContent = metrics.time || "-";
    }
}

async function handleAsk() {
    const question = elements.question.value.trim();
    if (!question) {
        setStatus("error", "Please enter a question");
        return;
    }

    setLoading(true);
    const startTime = performance.now();

    try {
        // Step 1: Get current tab
        setStatus("loading", "Extracting page content...");
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        // Step 2: Extract content from page
        const content = await chrome.tabs.sendMessage(tab.id, { type: "EXTRACT" });

        if (!content || !content.sections || content.sections.length === 0) {
            throw new Error("Could not extract content from this page");
        }

        // Step 3: Ingest content
        setStatus("loading", `Indexing ${content.sections.length} sections...`);
        const ingestResponse = await fetch(`${API_BASE}/content/ingest-page/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(content)
        });

        if (!ingestResponse.ok) {
            const error = await ingestResponse.text();
            throw new Error(`Ingest failed: ${error}`);
        }

        const ingestData = await ingestResponse.json();

        // Step 4: Ask question
        setStatus("loading", "Generating answer...");
        const askResponse = await fetch(`${API_BASE}/ai/ask/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: ingestData.context_id,
                question: question
            })
        });

        if (!askResponse.ok) {
            const error = await askResponse.text();
            throw new Error(`Ask failed: ${error}`);
        }

        const askData = await askResponse.json();
        const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);

        // Show success
        setStatus("success", "Answer ready");
        showAnswer(askData.answer, {
            sections: ingestData.section_count || content.sections.length,
            tokens: askData.usage?.total_tokens || "-",
            time: `${elapsed}s`
        });

    } catch (error) {
        console.error("Error:", error);
        setStatus("error", error.message || "Something went wrong");
        showAnswer(`Error: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

// Event listeners
elements.askBtn.addEventListener("click", handleAsk);

elements.question.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleAsk();
    }
});

// Focus input on load
elements.question.focus();
