const API_BASE = "https://sapi.alass.dev";

let treeData = null;
let startTime = 0;
let projectCount = 0;
let maxDepthReached = 0;

const elements = {
  input: document.getElementById("projectId"),
  buildBtn: document.getElementById("buildBtn"),
  depthSlider: document.getElementById("depthSlider"),
  depthValue: document.getElementById("depthValue"),
  progressSection: document.getElementById("progressSection"),
  progressFill: document.getElementById("progressFill"),
  progressText: document.getElementById("progressText"),
  stats: document.getElementById("stats"),
  treeContainer: document.getElementById("treeContainer"),
  treeOutput: document.getElementById("treeOutput"),
  error: document.getElementById("error"),
  expandAll: document.getElementById("expandAll"),
  collapseAll: document.getElementById("collapseAll"),
  downloadBtn: document.getElementById("downloadBtn"),
  optionsToggle: document.getElementById("optionsToggle"),
  advancedOptions: document.getElementById("advancedOptions"),
};

// Options toggle
elements.optionsToggle.addEventListener("click", () => {
  elements.advancedOptions.classList.toggle("visible");
  elements.optionsToggle.textContent =
    elements.advancedOptions.classList.contains("visible")
      ? "Hide advanced options"
      : "Show advanced options";
});

// Depth slider
elements.depthSlider.addEventListener("input", (e) => {
  elements.depthValue.textContent = e.target.value;
});

// Build button
elements.buildBtn.addEventListener("click", async () => {
  const id = elements.input.value.trim();
  if (!id) return alert("Please enter a project ID!");

  elements.error.innerHTML = "";
  elements.treeContainer.style.display = "none";
  elements.stats.style.display = "none";
  elements.progressSection.classList.add("active");
  elements.buildBtn.disabled = true;

  projectCount = 0;
  maxDepthReached = 0;
  startTime = Date.now();

  try {
    const maxDepth = parseInt(elements.depthSlider.value);
    updateProgress(0, "Starting...");

    treeData = await buildTree(id, 0, maxDepth);

    const buildTime = ((Date.now() - startTime) / 1000).toFixed(1);

    document.getElementById("totalProjects").textContent = projectCount;
    document.getElementById("maxDepthReached").textContent = maxDepthReached;
    document.getElementById("buildTime").textContent = buildTime + "s";

    elements.stats.style.display = "grid";
    elements.treeContainer.style.display = "block";
    elements.progressSection.classList.remove("active");

    renderTree(treeData);
  } catch (err) {
    console.error(err);
    elements.error.innerHTML = `<div class="error">❌ ${err.message}</div>`;
    elements.progressSection.classList.remove("active");
  }

  elements.buildBtn.disabled = false;
});

function updateProgress(percent, text) {
  elements.progressFill.style.width = percent + "%";
  elements.progressText.textContent = text;
}

async function fetchJSON(url, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url);
      if (res.ok) return res.json();
    } catch (e) {
      if (i === retries - 1) throw e;
    }
    await new Promise((r) => setTimeout(r, 500 * (i + 1)));
  }
  throw new Error(`Failed to fetch ${url}`);
}

async function fetchProject(id) {
  return fetchJSON(`${API_BASE}/projects/${id}`);
}

async function fetchAllRemixes(projectId) {
  let allRemixes = [];
  let offset = 0;
  const limit = 40;

  while (true) {
    const url = `${API_BASE}/projects/${projectId}/remixes?offset=${offset}&limit=${limit}`;
    const batch = await fetchJSON(url);
    if (!batch || batch.length === 0) break;

    allRemixes.push(...batch);
    offset += limit;

    if (batch.length < limit) break;
  }

  return allRemixes;
}

async function buildTree(projectId, depth = 0, maxDepth = 5) {
  const project = await fetchProject(projectId);
  projectCount++;
  maxDepthReached = Math.max(maxDepthReached, depth);

  updateProgress(
    Math.min((projectCount / 100) * 100, 95),
    `Fetched ${projectCount} projects...`
  );

  const node = {
    id: project.id,
    title: project.title || "Untitled",
    author: project.author?.username || "unknown",
    children: [],
    depth: depth,
  };

  const numRemixes = project.stats?.remixes || 0;
  if (numRemixes === 0 || depth >= maxDepth) return node;

  const remixes = await fetchAllRemixes(projectId);

  // Faster parallel processing with larger batches
  const batchSize = 10;
  for (let i = 0; i < remixes.length; i += batchSize) {
    const batch = remixes.slice(i, i + batchSize);
    const results = await Promise.allSettled(
      batch.map((remix) => buildTree(remix.id, depth + 1, maxDepth))
    );

    const children = results
      .filter((r) => r.status === "fulfilled")
      .map((r) => r.value);

    node.children.push(...children);
  }

  return node;
}

function renderTree(node) {
  elements.treeOutput.innerHTML = "";
  const ul = document.createElement("ul");
  renderNode(node, ul);
  elements.treeOutput.appendChild(ul);
}

function renderNode(node, parentElem) {
  const li = document.createElement("li");

  const nodeDiv = document.createElement("div");
  nodeDiv.className = `tree-node depth-${node.depth % 5}`;

  if (node.children.length > 0) {
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

  const authorSpan = document.createElement("span");
  authorSpan.className = "node-author";
  authorSpan.textContent = `by ${node.author}`;
  nodeDiv.appendChild(authorSpan);

  if (node.children.length > 0) {
    const countSpan = document.createElement("span");
    countSpan.className = "node-count";
    countSpan.textContent = `${node.children.length} remix${
      node.children.length !== 1 ? "es" : ""
    }`;
    nodeDiv.appendChild(countSpan);
  }

  li.appendChild(nodeDiv);

  if (node.children.length > 0) {
    const childUl = document.createElement("ul");
    node.children.forEach((child) => renderNode(child, childUl));
    li.appendChild(childUl);
  }

  parentElem.appendChild(li);
}

// Tree actions
elements.expandAll.addEventListener("click", () => {
  document.querySelectorAll(".tree li").forEach((li) => {
    li.classList.remove("collapsed");
    const btn = li.querySelector(".toggle-btn");
    if (btn) btn.textContent = "−";
  });
});

elements.collapseAll.addEventListener("click", () => {
  document.querySelectorAll(".tree li").forEach((li) => {
    if (li.querySelector("ul")) {
      li.classList.add("collapsed");
      const btn = li.querySelector(".toggle-btn");
      if (btn) btn.textContent = "+";
    }
  });
});

elements.downloadBtn.addEventListener("click", () => {
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
  result +=
    prefix + connector + `${node.title} (${node.id}) by ${node.author}\n`;

  const childPrefix = prefix + (isLast ? "    " : "│   ");
  node.children.forEach((child, i) => {
    result += treeToText(child, childPrefix, i === node.children.length - 1);
  });

  return result;
}
