const API_BASE = "https://backend.alass.dev";
let eventSource = null;
let streamClosedByClient = false;
let treeData = null;
let startTime = 0;
let totalNodes = 0;
let currentSortMode = "share-date-desc"; // default to newest first
let currentSearch = "";

const $ = (id) => document.getElementById(id);
const consoleWrap = $("console");
const consoleBody = $("consoleBody");
const treeOutput = $("treeOutput");
const treeEmpty = $("treeEmpty");

/* ----------------------------- console ----------------------------- */
function setConsoleMessage(message, type = "") {
  consoleBody.innerHTML = "";
  addConsoleMessage(message, type);
}

const MAX_CONSOLE_LINES = 50;

function addConsoleMessage(message, type = "") {
  const line = document.createElement("div");
  line.className = `console-line ${type}`;
  line.textContent = message;
  consoleBody.appendChild(line);

  // trim old lines so a giant tree doesnt grow the dom forever
  while (consoleBody.children.length > MAX_CONSOLE_LINES) {
    consoleBody.removeChild(consoleBody.firstChild);
  }
  consoleBody.scrollTop = consoleBody.scrollHeight;
}

function clearConsole() {
  consoleBody.innerHTML = "";
}

/* drop ALL refs to the stream so nothing keeps the closures (or the tab) alive */
function closeStream() {
  if (eventSource) {
    eventSource.onmessage = null;
    eventSource.onerror = null;
    eventSource.close();
    eventSource = null;
  }
}

/* ------------------------------ build ------------------------------ */
function buildTree() {
  const projectId = $("projectId").value.toString().trim();

  if (!projectId) {
    clearConsole();
    consoleWrap.classList.add("show");
    setConsoleMessage("Error: Please enter a Scratch project ID", "error");
    return;
  }

  const buildBtn = $("buildBtn");
  buildBtn.disabled = true;
  clearConsole();
  consoleWrap.classList.add("show");
  $("treeContainer").style.display = "none";
  $("stats").style.display = "none";

  setConsoleMessage("Connecting... this can take a bit", "info");
  startTime = Date.now();
  totalNodes = 0;

  try {
    closeStream();
    streamClosedByClient = false;

    eventSource = new EventSource(`${API_BASE}/build/${projectId}`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "complete") {
          const buildTime = ((Date.now() - startTime) / 1000).toFixed(1);

          setConsoleMessage(`${data.message}\n\nTotal nodes: ${data.total_nodes}`, "done");

          $("totalProjects").textContent = data.total_nodes;
          $("maxDepthReached").textContent = calculateMaxDepth(data.tree);
          $("buildTime").textContent = buildTime + "s";
          $("stats").style.display = "grid";

          treeData = data.tree;
          renderTree(treeData);
          $("treeContainer").style.display = "block";

          streamClosedByClient = true;
          closeStream();
          buildBtn.disabled = false;
          return;
        }

        if (data.type === "error") {
          setConsoleMessage(`❌ ${data.message}`, "error");
          streamClosedByClient = true;
          closeStream();
          buildBtn.disabled = false;
          return;
        }

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
      if (streamClosedByClient) return;
      setConsoleMessage("Connection error...", "error");
      closeStream();
      buildBtn.disabled = false;
    };
  } catch (error) {
    setConsoleMessage(`Error: ${error.message}`, "error");
    buildBtn.disabled = false;
  }
}

function calculateMaxDepth(node, depth = 0) {
  if (!node.children || node.children.length === 0) return depth;
  return Math.max(...node.children.map((child) => calculateMaxDepth(child, depth + 1)));
}

/* ----------------------------- sorting ----------------------------- */
function sortChildren(children, sortMode) {
  if (!children || children.length === 0) return children;
  const sorted = [...children];

  switch (sortMode) {
    case "share-date-desc":
      sorted.sort((a, b) => byDate(b) - byDate(a));
      break;
    case "share-date-asc":
      sorted.sort((a, b) => byDate(a) - byDate(b));
      break;
    case "remix-count-desc":
      sorted.sort((a, b) => kids(b) - kids(a));
      break;
    case "remix-count-asc":
      sorted.sort((a, b) => kids(a) - kids(b));
      break;
    case "none":
      return children;
    default:
      return sorted;
  }
  return sorted;
}
const kids = (n) => (n.children ? n.children.length : 0);
const byDate = (n) => (n.shared_date ? new Date(n.shared_date).getTime() : 0);

function fmtCount(n) {
  n = Number(n) || 0;
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "k";
  return String(n);
}

/* ---------------------------- rendering ---------------------------- */
function renderTree(node) {
  treeOutput.innerHTML = "";
  const ul = document.createElement("ul");
  renderNode(node, ul, 0);
  treeOutput.appendChild(ul);
  // no per-node click handlers — see the delegated listener below (keeps memory flat)
  applyFilter(currentSearch);
}

function renderNode(node, parentElem, depth) {
  const li = document.createElement("li");
  li.dataset.id = node.id;
  li.dataset.title = node.title || "";

  const childCount = node.children ? node.children.length : 0;

  const nodeDiv = document.createElement("div");
  nodeDiv.className = `tree-node depth-${depth % 5}${childCount >= 5 ? " popular" : ""}`;
  nodeDiv.dataset.id = node.id;

  if (childCount > 0) {
    const toggleBtn = document.createElement("button");
    toggleBtn.className = "toggle-btn";
    toggleBtn.dataset.action = "toggle";
    toggleBtn.textContent = "−";
    toggleBtn.setAttribute("aria-label", "toggle children");
    nodeDiv.appendChild(toggleBtn);
  }

  const titleSpan = document.createElement("span");
  titleSpan.className = "node-title";
  titleSpan.textContent = node.title;
  nodeDiv.appendChild(titleSpan);

  const idSpan = document.createElement("span");
  idSpan.className = "node-author";
  idSpan.textContent = `#${node.id}`;
  nodeDiv.appendChild(idSpan);

  if (node.likes) nodeDiv.appendChild(statPill("likes", "♥", node.likes));
  if (node.views) nodeDiv.appendChild(statPill("views", "👁", node.views));

  if (childCount > 0) {
    const countSpan = document.createElement("span");
    countSpan.className = "node-count";
    countSpan.textContent = `${childCount} remix${childCount !== 1 ? "es" : ""}`;
    nodeDiv.appendChild(countSpan);
  }

  li.appendChild(nodeDiv);

  if (childCount > 0) {
    const sortedChildren = sortChildren(node.children, currentSortMode);
    const childUl = document.createElement("ul");
    sortedChildren.forEach((child) => renderNode(child, childUl, depth + 1));
    li.appendChild(childUl);
  }

  parentElem.appendChild(li);
}

function statPill(kind, glyph, value) {
  const span = document.createElement("span");
  span.className = `node-stat ${kind}`;
  span.textContent = `${glyph} ${fmtCount(value)}`;
  return span;
}

/* one delegated handler for the whole tree instead of a closure per node */
treeOutput.addEventListener("click", (e) => {
  const toggle = e.target.closest(".toggle-btn");
  if (toggle) {
    const li = toggle.closest("li");
    li.classList.toggle("collapsed");
    toggle.textContent = li.classList.contains("collapsed") ? "+" : "−";
    return;
  }
  const nodeEl = e.target.closest(".tree-node");
  if (nodeEl && nodeEl.dataset.id) {
    window.open(`https://scratch.mit.edu/projects/${nodeEl.dataset.id}`, "_blank");
  }
});

/* ----------------------------- search ------------------------------ */
function highlight(span, text, q) {
  span.textContent = "";
  const lower = text.toLowerCase();
  let i = 0;
  while (i < text.length) {
    const idx = lower.indexOf(q, i);
    if (idx === -1) {
      span.appendChild(document.createTextNode(text.slice(i)));
      break;
    }
    if (idx > i) span.appendChild(document.createTextNode(text.slice(i, idx)));
    const mark = document.createElement("mark");
    mark.textContent = text.slice(idx, idx + q.length);
    span.appendChild(mark);
    i = idx + q.length;
  }
}

function applyFilter(rawQuery) {
  const q = (rawQuery || "").trim().toLowerCase();
  const items = treeOutput.querySelectorAll("li");

  // reset everything first
  items.forEach((li) => {
    li.classList.remove("hidden");
    const titleEl = li.querySelector(":scope > .tree-node > .node-title");
    if (titleEl) titleEl.textContent = li.dataset.title;
  });

  if (!q) {
    treeEmpty.style.display = "none";
    return;
  }

  const visible = new Set();
  items.forEach((li) => {
    const title = (li.dataset.title || "").toLowerCase();
    const id = li.dataset.id || "";
    if (title.includes(q) || id.includes(q)) {
      visible.add(li);
      // reveal & un-collapse the whole ancestor chain
      let parent = li.parentElement ? li.parentElement.closest("li") : null;
      while (parent) {
        visible.add(parent);
        parent.classList.remove("collapsed");
        const btn = parent.querySelector(":scope > .tree-node > .toggle-btn");
        if (btn) btn.textContent = "−";
        parent = parent.parentElement ? parent.parentElement.closest("li") : null;
      }
      // highlight the matched bit of the title
      if (title.includes(q)) {
        const titleEl = li.querySelector(":scope > .tree-node > .node-title");
        if (titleEl) highlight(titleEl, li.dataset.title, q);
      }
    }
  });

  items.forEach((li) => li.classList.toggle("hidden", !visible.has(li)));
  treeEmpty.style.display = visible.size ? "none" : "block";
}

/* ----------------------------- controls ---------------------------- */
$("sortSelect").addEventListener("change", (e) => {
  currentSortMode = e.target.value;
  if (treeData) renderTree(treeData);
});

let searchTimer = null;
$("searchInput").addEventListener("input", (e) => {
  currentSearch = e.target.value;
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => applyFilter(currentSearch), 120);
});

$("expandAll").addEventListener("click", () => {
  treeOutput.querySelectorAll("li").forEach((li) => {
    li.classList.remove("collapsed");
    const btn = li.querySelector(":scope > .tree-node > .toggle-btn");
    if (btn) btn.textContent = "−";
  });
});

$("collapseAll").addEventListener("click", () => {
  treeOutput.querySelectorAll("li").forEach((li) => {
    if (li.querySelector("ul")) {
      li.classList.add("collapsed");
      const btn = li.querySelector(":scope > .tree-node > .toggle-btn");
      if (btn) btn.textContent = "+";
    }
  });
});

$("downloadBtn").addEventListener("click", () => {
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
  let result = prefix + (isLast ? "└── " : "├── ") + `${node.title} (${node.id})\n`;
  const childPrefix = prefix + (isLast ? "    " : "│   ");
  if (node.children && node.children.length > 0) {
    const sortedChildren = sortChildren(node.children, currentSortMode);
    sortedChildren.forEach((child, i) => {
      result += treeToText(child, childPrefix, i === sortedChildren.length - 1);
    });
  }
  return result;
}

/* ------------------------------ misc ------------------------------- */
$("buildBtn").addEventListener("click", buildTree);

$("projectId").addEventListener("keypress", (e) => {
  if (e.key === "Enter") buildTree();
});

// FAQ accordions (delegated, no inline onclick needed)
document.querySelectorAll(".expandable-header").forEach((header) => {
  header.addEventListener("click", () => header.parentElement.classList.toggle("active"));
});

// cleanup on page close
window.addEventListener("beforeunload", closeStream);
