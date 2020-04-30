# ChattyBoi

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![Documentation Status](https://readthedocs.org/projects/chattyboi/badge/?version=latest)](https://chattyboi.readthedocs.io/en/latest/?badge=latest)

**ChattyBoi** - chat bot backend and UI that can support any chat platform.

By itself, ChattyBoi is more of a framework than a useful application. The "core", i.e. the base program, allows you to easily add _extensions_, which in turn can add platform integration, commands, new GUI elements, and much more.

In order to be useful as a chat bot, this application needs extra configuration. Some presets (pre-configured profiles that _are_ useful) and guides will be available when the base program is done.

## Notable features:

- Completely free and open-source.
- Thus, fully decentralized and hackable.
- ChattyBoi can do pretty much anything chat-related (and more, if there's an extension for it).
- There doesn't have to be a "default chat", the users of which have to link their accounts to other chat platforms.
- There are some pretty cool extensions. (Or, well, will be when the time comes). For example, there will be a command editor with its own scripting syntax.
- Tons of documentation, examples, and presets are planned.

___

### **Why do we need another bot?**
The main "selling" point for ChattyBoi is the fact that it's not platform-specific. Extensions give you the ability to abstract away platform-specific interactions, and instead write and run things that work everywhere. For example: a command only needs to know that some specific text was sent to a chat, and only needs to tell ChattyBoi to reply with some other text. The actual implementation of receiving and sending messages is left up to the other extension.

This means that that extensions don't have to be re-written just to support Twitch, Discord, IRC, etc., unless they use APIs specific to those platforms.

## Installation
The base program is not yet ready. However, you can test what is done so far by cloning the repository and launching the installer or manually copying the files.
For now, the installer only works on *nix systems (macOS, Linux, etc.), since it's just a shell script.

Requirements: Python 3.8+

If your Python command is something other than `python`, edit `install.sh` at line 35.
```
git clone https://github.com/selplacei/chattyboi.git && cd chattyboi/scripts
sh install.sh --help
```
___

### **Motivation**
A certain Twitch streamer was the main inspiration behind this project. Come over to [ZeeGee_](https://twitch.tv/zeegee_)
if you like variety streamers that have a nice smaller community!

## TODOs

- Improve the GUI: Dashboard that shows all active chats and allows sending messages to them; database viewer; config editor; extension list/info; about page; better profile selector, with creating profiles and configuring them before initialization; easier interaction with the GUI for extensions
- Generate docs for the code and write docs for extension developing
- Importing/exporting profiles and extensions
- Write some basic extensions:
  * Commands, without using ChattyScript
  * Basic moderation: permission levels, blacklisting, user tags (roles)
  * Discord integration (chat only)
  * Currency system and a gambling mini-game (for testing)
- Make a Windows installer
- Polish the UX and add any missing features
- Write more sophisticated extensions:
  * ChattyScript
  * Moderation
  * Commands, using ChattyScript and moderation
  * Twitch integration
  * Anything else to make this at least as good as DeepBot
  * Discord integration
  * Web dashboard to be used by chatters, which will be supported by some of these other extensions
  * Statistics
- When a somewhat stable release is made, add ChattyBoi to the AUR
- (Possibly) CLI mode, either as a parameter or a separate executable.
