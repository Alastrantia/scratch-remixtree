# scratch-remixtree 🫚

[![PyPI version](https://img.shields.io/pypi/v/remixtree)](https://pypi.org/project/remixtree/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Alastrantia](https://img.shields.io/badge/made_by-alastrantia-purple)](https://scratch.mit.edu/users/Alastrantia)
[![All tests](https://github.com/Alastrantia/scratch-remixtree/actions/workflows/test-cli.yml/badge.svg)](https://github.com/Alastrantia/scratch-remixtree/actions/workflows/test-cli.yml)

> Tools to rebuild Scratch's remix tree feature!  
> **🌐 Try the web version instantly:** https://remixtree.alass.dev  
> **#BringBackRemixTrees**

**Like it?** Star the repo to help others find it and make me feel good 🥺

## Demos :DD

<p align="center">
  <figure>
    <img src="demos/demo.gif" width="45%" alt="CLI demo" style="margin: 0 1%;">
    <img src="demos/webdemo.png" width="45%" alt="Web demo" style="margin: 0 1%;">
  </figure>
</p>

<p align="center">
  <b>CLI Version:</b> <a href="https://scratch.mit.edu/projects/948573479/">Project 948573479</a><br>
  <code>remixtree 948573479 --output tree.txt --verbose</code>
</p>

<p align="center">
  <b>Web Version:</b> Try it instantly at <a href="https://remixtree.alass.dev">remixtree.alass.dev</a>!
</p>


## What is this?

Scratch removed the remix tree feature without any warning... 
So, here we go again, as a webapp and a CLI!

This tool fetches a project's remixes and builds a tree showing how all the remixes connect, using the official scratch API.

## Features

- **Web version** built with `FastAPI`, **CLI** built with `rich`
- Async, can create large trees decently fast
- Optional verbose mode to go crazy (CLI-only)
- Save the full remix tree to a file if ya want to
- Supports max depth if you wanna show empathy for the Scratch Servers (CLI-only)
- Works on Linux, macOS, and Windows (Python 3.9+) (hopefully, if not, tell me)

---

## Installation for the CLI

### Recommended: using **pipx** (isolated, should-work):
```bash
pip install --user pipx
pipx install remixtree
```
### Alternatively:
```
pip install remixtree
```

## Basic Usage
(This is only for the CLI, the WebApp is pretty self-explanatory)

### Example:
```
remixtree 1223809053 --depth 3 --output tree_output.txt
```

### More options:
```
-h, --help: 
    get a list of flags like this one
-d, --depth:
    specify how deep the tree should go, default is unlimited
-v, --verbose:
    just try it, you'll see for yourself
-o, --output:
    probably the most important flag, specify where the tree should be saved
-c, --color:
    enable color coding by depth (disabled by default), will use rich color formatting
```

## Example Output
```
└── root(1196834984)
    ├── » planet b «(1198230426)
    │   └── » planet b « remix(1212924547)
    ├── Apex Construction (BB7 Entry)(1198230627)
    ├── pinnacle constructions(1198232264)
    ├── R1(1198238918)
    │   └── R1 remix(1223273999)
    ├── ⬠ equilux branding (1198261493)
    ├── BB7 -  Keystone Works(1198288240)
    ├── AEDIFI(1198372015)
    ├── Mace - BB7 R1(1198407780)
    ... 
```

## Feature Tracker

- [x] ASCII tree visualization
- [x] Async fetching
- [x] Depth limiting
- [x] Verbose mode
- [x] File output
- [x] Color coding
- [x] Interactive tree navigation (yes, but not the original tree yet)
- [ ] Export to JSON/CSV
- [x] Web interface
- [ ] Batch processing