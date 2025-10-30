# scratch-remixtree 🫚

[![PyPI version](https://img.shields.io/pypi/v/remixtree)](https://pypi.org/project/remixtree/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Alastrantia](https://img.shields.io/badge/made_by-alastrantia-purple)](https://scratch.mit.edu/users/Alastrantia)
[![All tests](https://github.com/Alastrantia/scratch-remixtree/actions/workflows/test-cli.yml/badge.svg)](https://github.com/Alastrantia/scratch-remixtree/actions/workflows/test-cli.yml)

> A simple CLI to rebuild Scratch’s remix tree feature, which was removed sometime around Mid-October 2025.  
> **#BringBackRemixTrees**

**Like this tool?** Star the repo to help others find it and make me feel good 🥺

## Demo :DD

<img src="demos/demo.gif" width="70%" alt="Small tree demo"><br>
>Project Link: https://scratch.mit.edu/projects/948573479/  
>Command: `remixtree 948573479 --output tree.txt --verbose`


## What is this?

Scratch removed the remix tree feature without any warning... 
So, here we go again, in the form of a CLI!

This CLI fetches a project’s remixes and builds a tree showing how all the remixes connect, using the official scratch API.


## Features

- Built with `rich`
- Async, can create large trees decently fast
- Optional verbose mode to go crazy
- Save the full remix tree to a file if ya want to
- Supports max depth if you wanna show empathy for the Scratch Servers
- Works on Linux, macOS, and Windows (Python 3.9+) (hopefully, if not, tell me)

---

## Installation

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
- [ ] Interactive tree navigation
- [ ] Visual tree using graphviz
- [ ] Export to JSON/CSV
- [ ] Web interface
- [ ] Batch processing

## Other people have made similar, maybe even cooler things!
- redspacecat made retree: https://retree.quuq.dev/
- CST1229 made treemix: https://cst1229.eu.org/treemix/

Check those out too!