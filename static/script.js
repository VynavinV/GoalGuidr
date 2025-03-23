// Auto-typing text effect
const textInput = document.getElementById("textInput")
const generateButton = document.getElementById("generateButton")

// Array of phrases to type
const phrases = [
  "What happens when a snowman gets angry?",
  "Tell me about dinosaurs...",
  "How do rainbows form?",
  "Why is the sky blue?",
  "Tell me a story about a brave knight",
  "What makes popcorn pop?",
  "How do planes fly?",
  "Why do leaves change color?",
  "What's inside a volcano?",
]

let phraseIndex = 0
let charIndex = 0
let isDeleting = false
let typingDelay = 100 // Delay between typing each character
let typingInterval // Store the interval ID so we can clear it later
let isTypingActive = true // Flag to track if typing animation is active

// Function to type text with backspacing effect
function typeText() {
  if (!isTypingActive) return // Stop if typing is no longer active

  const currentPhrase = phrases[phraseIndex]

  if (isDeleting) {
    // Backspacing
    textInput.value = currentPhrase.substring(0, charIndex - 1)
    charIndex--
    typingDelay = 50 // Faster when deleting
  } else {
    // Typing
    textInput.value = currentPhrase.substring(0, charIndex + 1)
    charIndex++
    typingDelay = 100 // Normal speed when typing
  }

  // If we've typed the full phrase
  if (!isDeleting && charIndex === currentPhrase.length) {
    isDeleting = true
    typingDelay = 1500 // Pause before starting to delete
  }
  // If we've deleted the full phrase
  else if (isDeleting && charIndex === 0) {
    isDeleting = false
    phraseIndex = (phraseIndex + 1) % phrases.length // Move to next phrase
    typingDelay = 500 // Pause before typing next phrase
  }

  typingInterval = setTimeout(typeText, typingDelay)
}

// Stop typing animation and clear the text
function stopTypingAnimation() {
  isTypingActive = false
  clearTimeout(typingInterval)
  textInput.value = "" // Clear the text
}

// Function to load conversation history
function loadConversationHistory() {
  fetch('/get-conversation-history')
    .then(response => response.json())
    .then(data => {
      if (data.conversation_history) {
        const chatLog = document.getElementById("chatLog");
        chatLog.style.display = "block"; // Ensure chat log is visible
        data.conversation_history.forEach(message => {
          const type = message.startsWith("User") ? "user" : "ai";
          const content = message.replace(/^User.*?:\s*/, "").replace(/^AI:\s*/, "");
          addMessageToChatLog(type, content);
        });
      }
    })
    .catch(error => console.error("Error loading conversation history:", error));
}

// Start the typing effect when the page loads
window.addEventListener("load", () => {
  loadConversationHistory();
  // Clear the placeholder
  textInput.placeholder = ""
  // Start typing effect
  isTypingActive = true
  setTimeout(typeText, 1000)
})

// Stop typing animation when the user focuses on the textarea
textInput.addEventListener("focus", () => {
  stopTypingAnimation()
})

// Create stop button
const stopButton = document.createElement("button");
stopButton.textContent = "Stop Recording";
stopButton.style.display = "none"; // Initially hidden
stopButton.id = "stopButton";
document.querySelector(".buttons-container").appendChild(stopButton);

// Create exit voice mode button
const exitVoiceModeButton = document.createElement("button");
exitVoiceModeButton.textContent = "Exit Voice Mode";
exitVoiceModeButton.style.display = "none"; // Initially hidden
exitVoiceModeButton.id = "exitVoiceModeButton";
document.querySelector(".buttons-container").appendChild(exitVoiceModeButton);

// Generate button event listener
generateButton.addEventListener("click", async () => {
  const userText = textInput.value;
  const canvas = document.getElementById("animationCanvas");
  const ctx = canvas.getContext("2d");
  const inputContainer = document.getElementById("input-container");

  if (!userText.trim()) {
    alert("Please enter some text.");
    return;
  }

  try {
    // Show the canvas without hiding the input container
    canvas.style.display = "block";

    // Add user message to chat log
    addMessageToChatLog("user", userText);

    const response = await fetch("/generate-frames", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: userText }),
    });

    if (!response.ok) {
      throw new Error("Failed to generate animation frames");
    }

    // Extract audio from the response headers
    const audioBase64 = response.headers.get("X-Audio-Base64");
    if (!audioBase64) {
      throw new Error("Audio data missing in response");
    }

    // Create an audio element and play the audio
    const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
    audio.play();

    // Fetch the AI response
    fetch("/get-last-response")
      .then((response) => response.json())
      .then((data) => {
        if (data.response) {
          addMessageToChatLog("ai", data.response);
        }
      })
      .catch((error) => console.error("Error getting AI response:", error));

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    const renderFrame = (base64Image) => {
      const img = new Image();
      img.src = base64Image;
      img.onload = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      };
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split("\n");
      buffer = frames.pop(); // Keep the last incomplete frame in the buffer

      for (const frame of frames) {
        if (frame.trim()) {
          renderFrame(frame.trim());
          await new Promise((resolve) => setTimeout(resolve, 1000 / 24)); // 24 FPS
        }
      }
    }
  } catch (error) {
    console.error(error);
    alert("An error occurred while generating the animation.");
  }
});

// Stop button event listener
stopButton.addEventListener("click", () => {
  const canvas = document.getElementById("animationCanvas");
  const inputContainer = document.getElementById("input-container");

  // Revert the UI back to its original state
  canvas.style.display = "none";
  inputContainer.style.display = "block";
  stopButton.style.display = "none";

  // Stop any ongoing audio or mic recording (if applicable)
  console.log("Recording stopped and UI reverted.");
});

// Exit voice mode button event listener
exitVoiceModeButton.addEventListener("click", () => {
  const canvas = document.getElementById("animationCanvas");
  const inputContainer = document.getElementById("input-container");

  // Revert the UI back to its original state
  canvas.style.display = "none";
  inputContainer.style.display = "block";
  exitVoiceModeButton.style.display = "none"; // Hide the exit button

  console.log("Exited voice mode.");
});

// Function to add messages to the chat log
function addMessageToChatLog(type, message) {
  const chatLog = document.getElementById("chatLog")
  const messageDiv = document.createElement("div")
  messageDiv.className = "chat-message"

  // Create message content based on type
  if (type === "user") {
    messageDiv.innerHTML = `<div class="user-message">You: ${message}</div>`
  } else if (type === "ai") {
    // Check if message is longer than 100 characters
    if (message.length > 100) {
      const truncatedMessage = message.substring(0, 100)
      const fullMessage = message

      // Create truncated message with expand button
      messageDiv.innerHTML = `
                <div class="ai-message">
                    <span>AI: </span>
                    <span class="message-content">${truncatedMessage}</span>
                    <span class="expand-button">...</span>
                </div>
            `

      // Add click event to expand button
      messageDiv.querySelector(".expand-button").addEventListener("click", function () {
        messageDiv.querySelector(".message-content").textContent = fullMessage
        this.style.display = "none"
      })
    } else {
      messageDiv.innerHTML = `<div class="ai-message">AI: ${message}</div>`
    }
  }

  // Add message to chat log
  chatLog.appendChild(messageDiv)

  // Scroll to bottom of chat log
  chatLog.scrollTop = chatLog.scrollHeight
}

console.log("Welcome to GoalGuidr!");