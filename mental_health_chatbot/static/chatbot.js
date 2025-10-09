function sendMessage() {
    const userInput = document.getElementById("userInput").value;
    if (userInput.trim() === "") return;

    const chatbox = document.getElementById("chatbox");
    chatbox.innerHTML += `<p><b>You:</b> ${userInput}</p>`;
    document.getElementById("userInput").value = "";

    fetch("/get", {
        method: "POST",
        body: new URLSearchParams({ msg: userInput }),
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
    })
    .then(res => res.json())
    .then(data => {
        chatbox.innerHTML += `<p><b>Bot:</b> ${data.response}</p>`;
        chatbox.scrollTop = chatbox.scrollHeight;
    });
}
