# scratch-remixtree 🫚

[![PyPI version](https://img.shields.io/pypi/v/remixtree)](https://pypi.org/project/remixtree/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Alastrantia](https://img.shields.io/badge/made_by-alastrantia-purple)](https://scratch.mit.edu/users/Alastrantia)
[![All tests](https://github.com/Alastrantia/scratch-remixtree/actions/workflows/test-cli.yml/badge.svg)](https://github.com/Alastrantia/scratch-remixtree/actions/workflows/test-cli.yml)

> A simple CLI to rebuild Scratch’s remix tree feature, which was removed sometime around Mid-October 2025.  
> **#BringBackRemixTrees**

---

## What is this?

Scratch removed the remix tree feature without any warning 😭.  
So, here we go again, in the form of a CLI

This CLI fetches a project’s remixes and builds a tree showing how all the remixes connect, using the official scratch API.

---

## Features

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
-o, --ouput:
    probably the most important flag, specify where the tree should be saved
```

## Example Output
```
└── 1189258928
    ├── 1214754181
    ├── 1214779807
    ├── 1214838754
    ├── 1214857130
    │   └── 1200011719
    │   └── 1200011719
    ├── 1214886381
    ├── 1214926629
    ├── 1215025153
    ├── 1215026630
    ├── 1215041586
    ├── 1215121740
```

(Project names, authors and other visualization options will be added later)