const API_BASE = "http://127.0.0.1:8000";
let eventSource = null;
let streamClosedByClient = false;

function toggleExpandable(header) {
  header.parentElement.classList.toggle("active");
}

function setConsoleMessage(message, type = "") {
  const consoleEl = document.getElementById("console");
  consoleEl.innerHTML = "";
  const line = document.createElement("div");
  line.className = `console-line ${type}`;
  line.textContent = message;
  consoleEl.appendChild(line);
  consoleEl.scrollTop = consoleEl.scrollHeight;
}

function clearConsole() {
  document.getElementById("console").innerHTML = "";
}

async function buildTree() {
  const projectId = document.getElementById("projectId").value.trim();

  if (!projectId) {
    clearConsole();
    document.getElementById("console").classList.add("show");
    setConsoleMessage("Error: Please enter a Scratch project ID", "error");
    return;
  }

  const buildBtn = document.getElementById("buildBtn");
  buildBtn.disabled = true;
  clearConsole();
  document.getElementById("console").classList.add("show");
  setConsoleMessage("Connecting...", "info");

  try {
    if (eventSource) eventSource.close();
    streamClosedByClient = false;

    const url = `${API_BASE}/build/${projectId}`;
    eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "complete") {
          setConsoleMessage(
            `✅ ${data.message}\n\nTotal nodes: ${data.total_nodes}`,
            "success"
          );
          streamClosedByClient = true;
          eventSource.close();
          buildBtn.disabled = false;
          return;
        }

        if (data.type === "error") {
          setConsoleMessage(`❌ ${data.message}`, "error");
          streamClosedByClient = true;
          eventSource.close();
          buildBtn.disabled = false;
          return;
        }

        // Progress or status updates
        setConsoleMessage(JSON.stringify(data, null, 2));
      } catch {
        setConsoleMessage(event.data);
      }
    };

    eventSource.onerror = () => {
      // Ignore if we closed it ourselves after completion
      if (streamClosedByClient) return;

      setConsoleMessage(
        "Connection error. Make sure the backend is running.",
        "error"
      );
      eventSource.close();
      eventSource = null;
      buildBtn.disabled = false;
    };
  } catch (error) {
    setConsoleMessage(`Error: ${error.message}`, "error");
    buildBtn.disabled = false;
  }
}

document.getElementById("projectId").addEventListener("keypress", (e) => {
  if (e.key === "Enter") buildTree();
});

window.addEventListener("beforeunload", () => {
  if (eventSource) eventSource.close();
});
