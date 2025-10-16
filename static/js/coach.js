// ===== Enhanced Mini AI Coach =====
function miniCoach(sessionResults) {
    if (!sessionResults || !sessionResults.length) return;

    // Get recent performance data
    const recent10 = sessionResults.slice(-10);
    const wrongCount = recent10.filter(r => r.status === "Wrong").length;
    const correctAttempts = recent10.filter(r => r.reactionTime !== "-");
    const allCorrectTimes = sessionResults.filter(r => r.reactionTime !== "-").map(r => r.reactionTime);
    
    let message = "";
    let emoji = "🤖";

    // No valid attempts yet
    if (correctAttempts.length === 0) {
        message = "Take your time to get the first correct response! 🎯";
        emoji = "💭";
    }
    // Check for too many mistakes
    else if (wrongCount >= 4) {
        message = "Slow down and focus on accuracy first! Speed comes with practice. ⚠️";
        emoji = "🎯";
    }
    // Analyze reaction time performance
    else if (correctAttempts.length > 0) {
        const recentAvg = correctAttempts.reduce((a, b) => a + b.reactionTime, 0) / correctAttempts.length;
        const lastReaction = correctAttempts[correctAttempts.length - 1].reactionTime;
        
        // Check for improvement
        if (correctAttempts.length >= 2) {
            const prevReaction = correctAttempts[correctAttempts.length - 2].reactionTime;
            const improvement = prevReaction - lastReaction;
            
            if (improvement > 50) {
                message = `🚀 Massive improvement! ${improvement}ms faster than last time!`;
                emoji = "⚡";
            } else if (improvement > 20) {
                message = `📈 Getting faster! You improved by ${improvement}ms!`;
                emoji = "🎯";
            } else if (improvement < -30) {
                message = "🤔 Take a breath and focus. Consistency is key!";
                emoji = "💭";
            }
        }
        
        // Performance level feedback
        if (!message) {
            if (recentAvg < 250) {
                message = "🏆 Elite reflexes! You're in the top 1%!";
                emoji = "👑";
            } else if (recentAvg < 350) {
                message = "🔥 Excellent reflexes! Keep this pace up!";
                emoji = "⚡";
            } else if (recentAvg < 450) {
                message = "💪 Good reaction time! Practice makes perfect!";
                emoji = "🎯";
            } else if (recentAvg < 600) {
                message = "📚 Getting there! Focus on anticipating the glow.";
                emoji = "💭";
            } else {
                message = "🧘 Relax and stay focused. Speed will come naturally!";
                emoji = "🤲";
            }
        }
        
        // Consistency check
        if (correctAttempts.length >= 5) {
            const times = correctAttempts.slice(-5).map(r => r.reactionTime);
            const variance = calculateVariance(times);
            if (variance > 15000 && recentAvg < 400) { // High variance but fast average
                message = "⚖️ You're fast but inconsistent. Try to find your rhythm!";
                emoji = "🎵";
            }
        }
        
        // Special achievements
        if (allCorrectTimes.length > 0) {
            const personalBest = Math.min(...allCorrectTimes);
            if (lastReaction === personalBest && personalBest < 300) {
                message = "🎉 NEW PERSONAL RECORD! That was lightning fast!";
                emoji = "🏅";
            }
        }
    }

    // Display message in coach box
    const coachBox = document.getElementById("coachBox");
    if (coachBox && message) {
        coachBox.innerHTML = `${emoji} ${message}`;
    }
    
    // Also send to chat sidebar
    if (message && typeof Chat !== 'undefined' && Chat.logAIFeedback) {
        Chat.logAIFeedback(`${emoji} ${message}`);
    }
}

// Helper function to calculate variance for consistency analysis
function calculateVariance(numbers) {
    if (numbers.length === 0) return 0;
    
    const mean = numbers.reduce((a, b) => a + b, 0) / numbers.length;
    const squaredDiffs = numbers.map(num => Math.pow(num - mean, 2));
    return squaredDiffs.reduce((a, b) => a + b, 0) / numbers.length;
}

// Advanced coaching function for multiplayer mode preparation
function multiplayerCoach(player1Results, player2Results) {
    const p1Avg = player1Results.length > 0 ? 
        player1Results.reduce((a, b) => a + b, 0) / player1Results.length : Infinity;
    const p2Avg = player2Results.length > 0 ? 
        player2Results.reduce((a, b) => a + b, 0) / player2Results.length : Infinity;
    
    if (p1Avg < p2Avg) {
        return "🥇 Player 1 is leading with faster average reaction time!";
    } else if (p2Avg < p1Avg) {
        return "🥇 Player 2 is leading with faster average reaction time!";
    } else {
        return "⚖️ It's a tie! Next reaction could decide the winner!";
    }
}