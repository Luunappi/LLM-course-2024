describe('Chat functionality', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="chat-messages"></div>
            <input id="message-input" />
            <button id="send-button"></button>
        `;
    });

    test('should add message to chat', () => {
        const message = 'Test message';
        addMessage(message, true);
        const messages = document.querySelectorAll('.message');
        expect(messages.length).toBe(1);
        expect(messages[0].textContent).toBe(message);
    });

    test('should clear input after sending', async () => {
        const input = document.getElementById('message-input');
        input.value = 'Test message';
        await sendMessage();
        expect(input.value).toBe('');
    });
}); 