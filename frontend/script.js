document.getElementById('send-btn').addEventListener('click', async () => {
    const queryInput = document.getElementById('query-input');
    const resultsDiv = document.getElementById('results');
    
    const queryText = queryInput.value;
    if (!queryText) {
        resultsDiv.innerHTML = "<p>Please enter a query.</p>";
        return;
    }
  
    // Send query to backend API
    try {
        const response = await fetch('http://127.0.0.1:5000/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: queryText })
        });
        const data = await response.json();
  
        // Display results in the frontend
        resultsDiv.innerHTML = "";
        data.results.forEach(result => {
            const resultDiv = document.createElement('div');
            resultDiv.innerHTML = `
                <p><strong>Question:</strong> ${result.instruction}</p>
                <p><strong>Answer:</strong> ${result.response}</p>
                <hr>
            `;
            resultsDiv.appendChild(resultDiv);
        });
    } catch (error) {
        console.error("Error fetching results:", error);
        resultsDiv.innerHTML = "<p>Something went wrong.</p>";
    }
  });
  