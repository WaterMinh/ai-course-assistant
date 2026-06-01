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

function addMessage(text, type) {
    const div = document.createElement("div");

    div.className = type === "user"
        ? "user-message"
        : "bot-message";

    const normalized = normalizeMath(text);
    div.innerHTML = escapeHtml(normalized).replace(/\n/g, "<br>");

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;

    renderMath(div);

    return div;
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
            const normalized = normalizeMath(data.answer);
            loading.innerHTML = escapeHtml(normalized).replace(/\n/g, "<br>");
            renderMath(loading);
        }
    } catch (err) {
        loading.textContent = "Cannot connect to backend or Ollama.";
    }

    loading.classList.remove("loading");
});