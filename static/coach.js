// ===== Mini AI Coach =====
function miniCoach(sessionResults) {
    if (!sessionResults || !sessionResults.length) return;

    // Compute metrics
    const wrongCount = sessionResults.filter(r => r.status === "Wrong").length;
    const validTimes = sessionResults.filter(r => r.reactionTime !== "-");
    const avgTime = validTimes.length
        ? (validTimes.reduce((a, b) => a + b.reactionTime, 0) / validTimes.length).toFixed(2)
        : null;

    let message = "";

    if (wrongCount > 3) message += "⚠ Too many mistakes, focus on accuracy. ";
    if (avgTime && avgTime < 400) message += "🎯 Your reaction is fast! Consider increasing difficulty. ";
    if (avgTime && avgTime > 600) message += "⏱ Try to react faster, keep practicing!";

    // Display message in status box
    const statusBox = document.getElementById("status");
    if (statusBox && message) statusBox.textContent = message;
}