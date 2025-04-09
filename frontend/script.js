document.addEventListener("DOMContentLoaded", () => {
  const queryInput = document.getElementById("query-input");
  const sendBtn = document.getElementById("send-btn");
  const resultsDiv = document.getElementById("results");
  const chatArea = document.getElementById("chat-area");
  const emergencyBtn = document.getElementById("emergency-btn");
  const emergencyNumbersDiv = document.getElementById("emergency-numbers");
  const tamilNaduList = document.getElementById("tamil-nadu-list");
  const indiaList = document.getElementById("india-list");
  const languageSelector = document.getElementById("language-select");
  const loadingOverlay = document.getElementById("loading-overlay");
  // Emergency numbers data
  const tamilNaduNumbers = [
    { name: "Police", number: "100 or 112" },
    { name: "Fire", number: "101" },
    { name: "Ambulance", number: "102 or 108" },
    { name: "Coastal Security Helpline", number: "1093" },
    { name: "Traffic Police", number: "103" },
    { name: "Women Helpline", number: "1091" },
    { name: "Child Line", number: "1098" },
    { name: "Railway Police Helpline", number: "9962500500 or 1512" },
    { name: "Disaster Helpline", number: "1070 or 1077" },
    { name: "Gas Leakage", number: "1716 or (011)-1906" },
    { name: "Anti Ragging Complain", number: "18001805522" },
    {
      name: "Depression and Suicide Prevention",
      number: "104 or (85265)65656",
    },
  ];

  const indiaNumbers = [
    { name: "National Emergency Number", number: "112" },
    { name: "Police", number: "100" },
    { name: "Fire", number: "101" },
    { name: "Ambulance", number: "102" },
    { name: "Disaster Management Services", number: "108" },
    { name: "Women Helpline (Domestic Abuse)", number: "181" },
    { name: "AIDS Helpline", number: "1097" },
    { name: "Anti Poison (New Delhi)", number: "1066" },
    { name: "Railway Accident Emergency Services", number: "1072" },
    { name: "Road Accident Emergency Services", number: "1073 or 1033" },
  ];
  // Function to show loading overlay
  function showInlineLoading() {
    const inlineLoading = document.getElementById("inline-loading");
    inlineLoading.classList.remove("hidden");
    const resultsDiv = document.getElementById("results");
    resultsDiv.appendChild(inlineLoading);
  }

  // Function to hide inline loading
  function hideInlineLoading() {
    const inlineLoading = document.getElementById("inline-loading");
    inlineLoading.classList.add("hidden");
  }
  // Function to populate emergency numbers list
  function populateList(listElement, data) {
    listElement.innerHTML = data
      .map((item) => `<li><strong>${item.name}</strong>: ${item.number}</li>`)
      .join("");
  }

  // Populate emergency numbers lists
  populateList(tamilNaduList, tamilNaduNumbers);
  populateList(indiaList, indiaNumbers);

  // Toggle emergency numbers dropdown
  emergencyBtn.addEventListener("click", () => {
    emergencyNumbersDiv.classList.toggle("hidden");
  });

  // Close dropdown when clicking outside
  document.addEventListener("click", (event) => {
    if (
      !emergencyBtn.contains(event.target) &&
      !emergencyNumbersDiv.contains(event.target)
    ) {
      emergencyNumbersDiv.classList.add("hidden");
    }
  });

  // Prevent dropdown from closing when clicking inside
  emergencyNumbersDiv.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  // Function to format timestamp
  const formatTime = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };
  // Function to add system messages
  const addSystemMessage = (message) => {
    const messageElement = document.createElement("div");
    messageElement.classList.add("system-message");
    messageElement.innerHTML = `
      <p>${message}</p>
      <span class="timestamp">${formatTime()}</span>
    `;
    resultsDiv.appendChild(messageElement);
    chatArea.scrollTop = chatArea.scrollHeight;
  };
  // Function to add user message
  const addUserMessage = (message) => {
    const messageElement = document.createElement("div");
    messageElement.classList.add("user-message");
    messageElement.innerHTML = `
            <p>${message}</p>
            <span class="timestamp">${formatTime()}</span>
        `;
    resultsDiv.appendChild(messageElement);
    chatArea.scrollTop = chatArea.scrollHeight;
  };

  // Function to add AI message with typing effect
  const addAIMessage = (message) => {
    const messageElement = document.createElement("div");
    messageElement.classList.add("ai-message", "typing");
    messageElement.innerHTML = `
          <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
          </div>
      `;
    resultsDiv.appendChild(messageElement);
    chatArea.scrollTop = chatArea.scrollHeight;

    // Simulate typing effect
    setTimeout(() => {
      // Preserve line breaks by replacing "\n" with "<br>"
      messageElement.innerHTML = `
              <p>${message.replace(/\n/g, "<br>")}</p>
              <span class="timestamp">${formatTime()}</span>
          `;
      messageElement.classList.remove("typing");
      chatArea.scrollTop = chatArea.scrollHeight;
    }, 1500);
  };

  // Language Selector Event Listener
  languageSelector.addEventListener("change", async function () {
    let selectedLanguage = this.value;
    try {
      const response = await fetch("http://localhost:5000/set-language", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ language: selectedLanguage }),
      });

      console.log("Response status:", response.status);

      if (!response.ok) {
        // Try to get more error details
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(
          `HTTP error! status: ${response.status}, message: ${errorText}`
        );
      }

      const data = await response.json();
      console.log("Language set to:", data.language);

      // Optional: Show a success message
      addAIMessage(`Language changed to ${selectedLanguage}`);
    } catch (error) {
      console.error("Detailed error setting language:", error);

      // More informative error message
      addAIMessage(`Sorry, there was an issue changing the language. 
  Error details: ${error.message}. 
  Please check your server connection.`);
    }
  });

  // Function to handle sending message
  const sendMessage = async () => {
    const queryText = queryInput.value.trim();

    if (!queryText) {
      addSystemMessage("⚠️ Please enter a valid query.");
      return;
    }
    // Add user message
    addUserMessage(queryText);
    queryInput.value = "";

    // Show inline loading
    showInlineLoading();

    try {
      const response = await fetch("http://127.0.0.1:5000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: queryText }),
      });
      const data = await response.json();

      // Log contexts for debugging
      console.log("Top 3 Relevant Contexts:", data.contexts);

      // Add AI response with typing effect
      addAIMessage(data.answer);
    } catch (error) {
      console.error("Error:", error);
      addSystemMessage("🤖 Sorry, something went wrong. Please try again.");
    } finally {
      // Hide inline loading
      hideInlineLoading();
    }
  };

  // Event Listeners
  sendBtn.addEventListener("click", sendMessage);
  queryInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });

  // Function to handle phone number dialing
  function dialPhoneNumber(phoneNumber) {
    // Remove any non-digit characters
    const cleanedNumber = phoneNumber.replace(/\D/g, "");

    // Create a phone call link
    const phoneLink = document.createElement("a");
    phoneLink.href = `tel:${cleanedNumber}`;

    // Programmatically click the link to initiate call
    phoneLink.click();
  }

  // Modify the existing event listeners to support phone dialing
  resultsDiv.addEventListener("click", (event) => {
    // Check if the clicked element contains a phone number link
    const phoneLink = event.target.closest('a[href^="tel:"]');

    if (phoneLink) {
      event.preventDefault(); // Prevent default link behavior
      const phoneNumber = phoneLink.getAttribute("href").replace("tel:", "");
      dialPhoneNumber(phoneNumber);
    }
  });

  // Function to get user's current location with improved accuracy
  function getCurrentLocation() {
    return new Promise((resolve, reject) => {
      if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              lat: position.coords.latitude,
              lng: position.coords.longitude,
            });
          },
          (error) => {
            console.error("Geolocation error:", error);
            reject(error);
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0,
          }
        );
      } else {
        reject(new Error("Geolocation is not supported by this browser."));
      }
    });
  }

  // Modified searchNearbyPoliceStations to use inline loading
  async function searchNearbyPoliceStations() {
    try {
      addUserMessage("Find nearby police stations");

      // Show inline loading
      showInlineLoading();

      const location = await getCurrentLocation();
      console.log("Current Location:", location);

      const response = await fetch(
        "http://127.0.0.1:5000/nearby-police-stations",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            latitude: location.lat,
            longitude: location.lng,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch nearby police stations");
      }

      const data = await response.json();

      // Add the stations list as an AI message
      addAIMessage(data.answer);
    } catch (error) {
      console.error("Error searching nearby police stations:", error);
      addAIMessage(`Error finding police stations: ${error.message}`);
    } finally {
      // Hide inline loading
      hideInlineLoading();
    }
  }

  // Add event listener for finding police stations
  const findPoliceStationsBtn = document.getElementById(
    "find-police-stations-btn"
  );
  if (findPoliceStationsBtn) {
    findPoliceStationsBtn.addEventListener("click", searchNearbyPoliceStations);
  }

  // New function to search nearby hospitals
  async function searchNearbyHospitals() {
    try {
      addUserMessage("Find nearby hospitals");

      // Show inline loading
      showInlineLoading();

      const location = await getCurrentLocation();
      console.log("Current Location:", location);

      const response = await fetch("http://127.0.0.1:5000/nearby-hospitals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          latitude: location.lat,
          longitude: location.lng,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch nearby hospitals");
      }

      const data = await response.json();

      // Add the hospitals list as an AI message
      addAIMessage(data.answer);
    } catch (error) {
      console.error("Error searching nearby hospitals:", error);
      addAIMessage(`Error finding hospitals: ${error.message}`);
    } finally {
      // Hide inline loading
      hideInlineLoading();
    }
  }

  // Add event listener for finding hospitals
  const findHospitalsBtn = document.getElementById("find-hospitals-btn");
  if (findHospitalsBtn) {
    findHospitalsBtn.addEventListener("click", searchNearbyHospitals);
  }
});
