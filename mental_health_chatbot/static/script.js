document.addEventListener('DOMContentLoaded', function() {
    console.log('SAATHI Chat Bot initialized');
    
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const clearChatBtn = document.getElementById('clearChat');

    // Send message
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        try {
            console.log('Sending message:', message);
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            if (data.success) {
                console.log('Message sent successfully');
                // Reload the page to show updated chat
                window.location.reload();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Network error. Please check console for details.');
        }
    });

    // Clear chat
    clearChatBtn.addEventListener('click', async function() {
        if (confirm('Clear all chat history?')) {
            try {
                const response = await fetch('/clear_chat', {
                    method: 'POST'
                });
                
                const data = await response.json();
                if (data.success) {
                    window.location.reload();
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error clearing chat.');
            }
        }
    });
});