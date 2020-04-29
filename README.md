# ChattyBoi

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![Documentation Status](https://readthedocs.org/projects/chattyboi/badge/?version=latest)](https://chattyboi.readthedocs.io/en/latest/?badge=latest)

**ChattyBoi** - chat bot backend and UI that can support any chat platform.

The base program, a.k.a. the "core", doesn't provide much functionality other than making it easy to add your own. Useful features, such as platform integration, commands, or GUI elements can be added as _extensions_. This repository contains the core; in order to be useful, it needs extra configuration. Some presets and basic guides will be available when the base program is done.

## Notable features:

- Completely free and open-source.
- As a result, fully decentralized and hackable.
- ChattyBoi can do pretty much anything chat-related (and more, if you know Python).
- There doesn't have to be a "default chat", the users of which have to link their accounts to other chat platforms.
- There are some pretty cool extensions. (Or, well, will be when the time comes). For example, there will be a command editor with its own scripting syntax.
- Tons of documentation, examples, and presets are planned.

___

### **Why do we need another bot?**
The main "selling" point for ChattyBoi is the fact that it's not platform-specific. Extensions give you the ability to abstract away platform-specific interactions, and instead write and run things that work everywhere. This means that that extensions don't have to be re-written just to support Twitch, Discord, IRC, etc., unless they use APIs specific to those platforms.

___
### **Installation**
The base program is not yet ready. However, you can test what is done so far by cloning the repository and launching the installer or manually copying the files.
For now, the installer only works on *nix systems (macOS, Linux, etc.) - it's just a shell script.

Requirements: Python 3.7+

If your Python command is something other than `python`, edit `install.sh` at line 35.
```
git clone https://github.com/selplacei/chattyboi.git && cd chattyboi/installer
sh install.sh --help
```
___

### **Motivation**
A certain Twitch streamer was the main inspiration behind this project. Come over to [ZeeGee_](https://twitch.tv/zeegee_)
if you like variety streamers that have a nice smaller community!
