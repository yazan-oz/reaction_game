// ===== Charts Module =====
const Charts = {
  
  reactionChart: null,

  initChart() {
    const ctx = document.getElementById('reactionChart').getContext('2d');
    this.reactionChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Reaction Time (ms)',
            data: [],
            borderColor: '#2ecc71',
            backgroundColor: 'rgba(46, 204, 113, 0.2)',
            tension: 0.2,
            fill: true
          },
          {
            label: 'Accuracy (1=Correct, 0=Wrong)',
            data: [],
            borderColor: '#3498db',
            backgroundColor: 'rgba(52, 152, 219, 0.2)',
            tension: 0.2,
            fill: false,
            yAxisID: 'accuracy'
          }
        ]
      },
      options: { 
        responsive: true, 
        scales: { 
          y: { 
            beginAtZero: true,
            title: { display: true, text: 'Reaction Time (ms)' }
          },
          accuracy: {
            type: 'linear',
            display: true,
            position: 'right',
            min: 0,
            max: 1,
            title: { display: true, text: 'Accuracy' }
          }
        }
      }
    });
  },

  updateChart() {
    if (!this.reactionChart) return;
    
    this.reactionChart.data.labels = GameState.sessionResults.map(r => `R${r.round}`);
    this.reactionChart.data.datasets[0].data = GameState.sessionResults.map(r => 
      r.reactionTime === "-" ? null : r.reactionTime
    );
    this.reactionChart.data.datasets[1].data = GameState.sessionResults.map(r => 
      r.status === "Correct" ? 1 : 0
    );
    this.reactionChart.update();
  }
};

