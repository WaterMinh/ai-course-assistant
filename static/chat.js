const form = document.getElementById("chatForm");
const input = document.getElementById("questionInput");
const chatBox = document.getElementById("chatBox");

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function normalizeMath(text) {
    return text
        .replace(/\\\\\[/g, "\\[")
        .replace(/\\\\\]/g, "\\]")
        .replace(/\\\\\(/g, "\\(")
        .replace(/\\\\\)/g, "\\)")
        .replace(/\\\\frac/g, "\\frac");
}

async function renderMath(element) {
    if (window.MathJax && window.MathJax.startup) {
        await window.MathJax.startup.promise;
        await window.MathJax.typesetPromise([element]);
    }
}

function addMessage(text, sender) {
    const row = document.createElement("div");
    row.className = sender === "user"
        ? "chat-row user-row"
        : "chat-row bot-row";

    const bubble = document.createElement("div");
    bubble.className = sender === "user"
        ? "chat-bubble user-message"
        : "chat-bubble bot-message";

    bubble.textContent = text;

    row.appendChild(bubble);
    chatBox.appendChild(row);

    chatBox.scrollTop = chatBox.scrollHeight;

    return bubble;
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const question = input.value.trim();

    if (!question) {
        return;
    }

    addMessage(question, "user");
    input.value = "";

    const loading = addMessage("AI is thinking...", "bot");
    loading.classList.add("loading");

    try {
        const apiUrl = window.CHAT_API_URL || "/api/chat";

        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question
            })
        });

        const data = await response.json();

        if (!response.ok) {
            loading.textContent = data.error || "Error";
        } else {
            const normalized = normalizeMath(data.answer || "No answer received.");
            loading.innerHTML = escapeHtml(normalized).replace(/\n/g, "<br>");
            await renderMath(loading);
        }
    } catch (err) {
        loading.textContent = "Cannot connect to backend or LM Studio.";
        console.error(err);
    }

    loading.classList.remove("loading");
    chatBox.scrollTop = chatBox.scrollHeight;
});