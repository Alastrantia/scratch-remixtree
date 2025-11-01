const API_BASE = "https://sapi.alass.dev"; // cors proxo

const input = document.getElementById("projectId");
const button = document.getElementById("buildBtn");
const status = document.getElementById("status");
const container = document.getElementById("treeContainer");

button.addEventListener("click", async () => {
  const id = input.value.trim();
  if (!id) return alert("Please enter a project ID.");

  status.textContent = "Building remix tree...";
  container.innerHTML = "";

  try {
    const tree = await buildTree(id, 0, 99);
    status.textContent = "Done!";
    renderTree(tree, container);
  } catch (err) {
    console.error(err);
    status.textContent = "❌ " + err.message;
  }
});


async function fetchJSON(url, retries = 3) {
  for (let i = 0; i < retries; i++) {
    const res = await fetch(url);
    if (res.ok) return res.json();
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
    if (!batch.length) break;

    allRemixes.push(...batch);
    offset += limit;

    await new Promise((r) => setTimeout(r, 0));
  }

  return allRemixes;
}

// recusive, parallel :sunglasses:
async function buildTree(projectId, depth = 0, maxDepth = 5) {
  const project = await fetchProject(projectId);
  const node = {
    id: project.id,
    title: project.title,
    author: project.author?.username || "unknown",
    children: [],
  };

  // skip if no remixes
  const numRemixes = project.stats?.remixes || 0;
  if (numRemixes === 0 || depth >= maxDepth) return node;

  const remixes = await fetchAllRemixes(projectId);

  // maybe make this higher?
  const batchSize = 5;
  for (let i = 0; i < remixes.length; i += batchSize) {
    const batch = remixes.slice(i, i + batchSize);
    const children = await Promise.all(
      batch.map(async (remix) => {
        try {
          return await buildTree(remix.id, depth + 1, maxDepth);
        } catch (err) {
          console.warn("Skipping remix", remix.id, err);
          return null;
        }
      })
    );
    node.children.push(...children.filter((c) => c));
    await new Promise((r) => setTimeout(r, 0));
  }

  return node;
}

// progressive DOM rendering
function renderTree(node, parentElem) {
  const ul = document.createElement("ul");
  const li = document.createElement("li");
  li.innerHTML = `<strong>${node.title}</strong> <span class="author">by ${node.author}</span>`;
  ul.appendChild(li);

  if (node.children && node.children.length > 0) {
    const childList = document.createElement("ul");
    node.children.forEach((child) => renderTree(child, childList));
    li.appendChild(childList);
  }

  parentElem.appendChild(ul);
}
