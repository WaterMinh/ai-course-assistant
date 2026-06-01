const form = document.getElementById("chatForm");
const input = document.getElementById("questionInput");
const chatBox = document.getElementById("chatBox");

function addMessage(text, type) {
    const div = document.createElement("div");

    div.className = type === "user"
        ? "user-message"
        : "bot-message";

    div.textContent = text;

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;

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
            loading.textContent = data.answer;
        }
    } catch (err) {
        loading.textContent = "Cannot connect to backend or Ollama.";
    }

    loading.classList.remove("loading");
});