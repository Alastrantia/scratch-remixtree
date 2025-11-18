const API_BASE = "https://backend.alass.dev";
let eventSource = null;
let streamClosedByClient = false;
let treeData = null;
let startTime = 0;
let totalNodes = 0;
let maxDepth = 0;
let currentSortMode = 'share-date-desc'; // default to newest first

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

const MAX_CONSOLE_LINES = 50;

function addConsoleMessage(message, type = "") {
  const consoleEl = document.getElementById("console");
  const line = document.createElement("div");
  line.className = `console-line ${type}`;
  line.textContent = message;
  consoleEl.appendChild(line);
  
  // remove old lines to prevent browser destruction
  while (consoleEl.children.length > MAX_CONSOLE_LINES) {
    consoleEl.removeChild(consoleEl.firstChild);
  }
  
  consoleEl.scrollTop = consoleEl.scrollHeight;
}

function clearConsole() {
  document.getElementById("console").innerHTML = "";
}

async function buildTree() {
  const projectId = document.getElementById("projectId").value.toString().trim();

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
  document.getElementById("treeContainer").style.display = "none";
  document.getElementById("stats").style.display = "none";
  
  setConsoleMessage("Connecting... this can take a bit", "info");
  startTime = Date.now();
  totalNodes = 0;
  maxDepth = 0;

  try {
    if (eventSource) eventSource.close();
    streamClosedByClient = false;

    const url = `${API_BASE}/build/${projectId}`;
    eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "complete") {
          const buildTime = ((Date.now() - startTime) / 1000).toFixed(1);
          
          setConsoleMessage(
            `${data.message}\n\nTotal nodes: ${data.total_nodes}`,
            "done"
          );
          
          // update stats
          document.getElementById("totalProjects").textContent = data.total_nodes;
          document.getElementById("maxDepthReached").textContent = calculateMaxDepth(data.tree);
          document.getElementById("buildTime").textContent = buildTime + "s";
          document.getElementById("stats").style.display = "grid";
          
          // render the tree
          treeData = data.tree;
          renderTree(treeData);
          document.getElementById("treeContainer").style.display = "block";
          
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

        // progress updates from SSE
        if (data.type === "progress") {
          addConsoleMessage(
            `Processing: ${data.node.title} (depth ${data.node.depth}, ${data.node.children_count} remixes)`,
            "info"
          );
        } else if (data.type === "status") {
          addConsoleMessage(data.message, "info");
        }
      } catch {
        addConsoleMessage(event.data);
      }
    };

    eventSource.onerror = () => {
      // ignore if we closed it ourselves
      if (streamClosedByClient) return;

      setConsoleMessage(
        "Connection error...",
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

function calculateMaxDepth(node, depth = 0) {
  if (!node.children || node.children.length === 0) {
    return depth;
  }
  return Math.max(...node.children.map(child => calculateMaxDepth(child, depth + 1)));
}

// sorting logic for the tree
function sortChildren(children, sortMode) {
  if (!children || children.length === 0) return children;
  
  const sorted = [...children];
  
  switch (sortMode) {
    case 'share-date-desc':
      sorted.sort((a, b) => {
        if (!a.shared_date) return 1;
        if (!b.shared_date) return -1;
        return new Date(b.shared_date) - new Date(a.shared_date);
      });
      break;
      
    case 'share-date-asc':
      sorted.sort((a, b) => {
        if (!a.shared_date) return 1;
        if (!b.shared_date) return -1;
        return new Date(a.shared_date) - new Date(b.shared_date);
      });
      break;
      
    case 'remix-count-desc':
      sorted.sort((a, b) => {
        const aCount = a.children ? a.children.length : 0;
        const bCount = b.children ? b.children.length : 0;
        return bCount - aCount;
      });
      break;
      
    case 'remix-count-asc':
      sorted.sort((a, b) => {
        const aCount = a.children ? a.children.length : 0;
        const bCount = b.children ? b.children.length : 0;
        return aCount - bCount;
      });
      break;
      
    case 'none':
      // no sorting, keep original order
      return children;
      
    default:
      return sorted;
  }
  
  return sorted;
}

function renderTree(node) {
  const treeOutput = document.getElementById("treeOutput");
  treeOutput.innerHTML = "";
  const ul = document.createElement("ul");
  renderNode(node, ul, 0);
  treeOutput.appendChild(ul);
}

function renderNode(node, parentElem, depth) {
  const li = document.createElement("li");

  const nodeDiv = document.createElement("div");
  const childCount = node.children ? node.children.length : 0;
  nodeDiv.className = `tree-node depth-${depth % 5}${childCount >= 5 ? ' popular' : ''}`;
  
  nodeDiv.style.cursor = "pointer";
  nodeDiv.onclick = (e) => {
    // don't redirect if clicking the expand button
    if (e.target.classList.contains("toggle-btn")) return;
    window.open(`https://scratch.mit.edu/projects/${node.id}`, "_blank");
  };

  if (node.children && node.children.length > 0) {
    const toggleBtn = document.createElement("button");
    toggleBtn.className = "toggle-btn";
    toggleBtn.textContent = "−";
    toggleBtn.onclick = (e) => {
      e.stopPropagation();
      li.classList.toggle("collapsed");
      toggleBtn.textContent = li.classList.contains("collapsed") ? "+" : "−";
    };
    nodeDiv.appendChild(toggleBtn);
  }

  const titleSpan = document.createElement("span");
  titleSpan.className = "node-title";
  titleSpan.textContent = node.title;
  nodeDiv.appendChild(titleSpan);

  const idSpan = document.createElement("span");
  idSpan.className = "node-author";
  idSpan.textContent = `ID: ${node.id}`;
  nodeDiv.appendChild(idSpan);

  if (node.children && node.children.length > 0) {
    const countSpan = document.createElement("span");
    countSpan.className = "node-count";
    countSpan.textContent = `${node.children.length} remix${
      node.children.length !== 1 ? "es" : ""
    }`;
    nodeDiv.appendChild(countSpan);
  }

  li.appendChild(nodeDiv);

  if (node.children && node.children.length > 0) {
    // apply the current sort mode
    const sortedChildren = sortChildren(node.children, currentSortMode);
    
    const childUl = document.createElement("ul");
    sortedChildren.forEach((child) => renderNode(child, childUl, depth + 1));
    li.appendChild(childUl);
  }

  parentElem.appendChild(li);
}

// sort dropdown change handler
document.getElementById("sortSelect").addEventListener("change", (e) => {
  currentSortMode = e.target.value;
  if (treeData) {
    renderTree(treeData); // re-render with new sort
  }
});

// expand/collapse buttons
document.getElementById("expandAll").addEventListener("click", () => {
  document.querySelectorAll(".tree li").forEach((li) => {
    li.classList.remove("collapsed");
    const btn = li.querySelector(".toggle-btn");
    if (btn) btn.textContent = "−";
  });
});

document.getElementById("collapseAll").addEventListener("click", () => {
  document.querySelectorAll(".tree li").forEach((li) => {
    if (li.querySelector("ul")) {
      li.classList.add("collapsed");
      const btn = li.querySelector(".toggle-btn");
      if (btn) btn.textContent = "+";
    }
  });
});

// download as text file
document.getElementById("downloadBtn").addEventListener("click", () => {
  if (!treeData) return;

  const text = treeToText(treeData);
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `remixtree-${treeData.id}.txt`;
  a.click();
  URL.revokeObjectURL(url);
});

function treeToText(node, prefix = "", isLast = true) {
  let result = "";
  const connector = isLast ? "└── " : "├── ";
  result += prefix + connector + `${node.title} (${node.id})\n`;

  const childPrefix = prefix + (isLast ? "    " : "│   ");
  if (node.children && node.children.length > 0) {
    // use the current sort mode for text export too
    const sortedChildren = sortChildren(node.children, currentSortMode);
    sortedChildren.forEach((child, i) => {
      result += treeToText(child, childPrefix, i === sortedChildren.length - 1);
    });
  }

  return result;
}

// enter key to build
document.getElementById("projectId").addEventListener("keypress", (e) => {
  if (e.key === "Enter") buildTree();
});

// cleanup on page close
window.addEventListener("beforeunload", () => {
  if (eventSource) eventSource.close();
});
