document.getElementById('sendMessage').addEventListener('click', async () => {
    const language = document.getElementById('languageSelect').value;
    const userMessage = document.getElementById('userMessage').value;

    if (!userMessage.trim()) {
        alert('Please enter a message.');
        return;
    }

    try {
        const response = await fetch('/gemini-conversation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ language, message: userMessage })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to get response from AI');
        }

        const data = await response.json();
        const conversationDiv = document.getElementById('conversation');
        const userMessageElement = document.createElement('p');
        userMessageElement.innerHTML = `<strong>You:</strong> ${userMessage}`;
        conversationDiv.appendChild(userMessageElement);

        const aiResponseElement = document.createElement('p');
        aiResponseElement.innerHTML = `<strong>AI:</strong> ${data.response}`;
        conversationDiv.appendChild(aiResponseElement);

        document.getElementById('userMessage').value = '';
    } catch (error) {
        console.error(error);
        alert(`Error: ${error.message}`);
    }
});
