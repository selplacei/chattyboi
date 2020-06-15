# ChattyBoi

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![Documentation Status](https://readthedocs.org/projects/chattyboi/badge/?version=latest)](https://chattyboi.readthedocs.io/en/latest/?badge=latest)

**ChattyBoi** - chat bot application/framework that can support any chat platform.

The base application defines things like a user, a chat, a message, etc., and provides easy ways for extensions to store data in a database, keep track of configs, and interact with each other. Additionally, the ChattyBoi launcher lets you store different profiles (instances of data and preferences), and the main application wraps everything into a graphical interface.

In order to be useful as a chat bot, this application needs configuration. Some guides and presets will be available when the base program is done: among them, a basic general-purpose bot, a generic Discord bot, and a Twitch streamer assistant.

## Notable features:

- Completely free and open-source
- Fully decentralized
- Based on asyncio and Qt
- Platform-independent
- There doesn't have to be a "default chat", whose users must link their accounts to other chat platforms in order to use them
- There is a huge potential for the extension ecosystem, since they can be used in any way for any purpose

Additionally, there will be some nice extensions:

- Commands: the concepts of an "action" and a "trigger" are separated, and neither are tied to some limited set of functionality. In other words, commands can do anything; and, if needed, they can be executed in a variety of ways.
- Moderation: user roles, tags, permission levels, blacklisting, configurable defaults, integration with commands and statistics.
- ChattyBoi Script: a custom scripting syntax to make commands more flexible; fairly simple, so you don't have to learn Python to write them.
- Full Twitch and Discord integration.
- Web dashboard: other extensions can use this to interact with chatters and moderators in a much cleaner and easier way than just commands.

___

### **Why do we need another bot?**
One of the main selling points for ChattyBoi is that it's platform-independent. Extensions give you the ability to abstract away platform-specific interactions, and instead write and run things that work everywhere. For example, a command might only need to know that some specific text was sent to a chat and tell ChattyBoi to reply with some other text. The implementations of actually receiving and sending messages through that chat are left up to another extension.

This means that that extensions don't have to be re-written just to support Twitch, Discord, IRC, etc., unless they use APIs specific to those platforms.

## Installation
You can play around with what is done so far by cloning the repository and launching the installer or manually copying the files.
The current installer is just for testing purposes, so it's just a shell script and will only work on Unix-like systems (macOS, Linux, etc).

Requirements: Python 3.8+

If your Python command is something other than `python`, edit `install.sh` at line 35.
```
git clone https://github.com/selplacei/chattyboi.git && cd chattyboi/scripts
sh install.sh --help
```
___

### **Motivation**
A certain Twitch streamer was the main inspiration behind this project. Come over to [ZeeGee_](https://twitch.tv/zeegee_) if you like variety streamers that have a nice smaller community!

## TODOs

- Improve the GUI: database viewer; config editor; extension list/info; better launcher, with creating profiles and configuring them before initialization; easier interaction with the GUI for extensions
- Generate docs for the code and write docs for extension developing
- Importing/exporting profiles and extensions
- Polish the UX and add any missing features
- Write extensions:
  * ChattyBoiScript
  * Moderation
  * Advanced Commands
  * Twitch integration
  * Anything else to make this at least as good as DeepBot
  * Discord integration
  * Web dashboard to be used by chatters, which will be supported by some of these other extensions
  * Statistics
- When a somewhat stable release is made, add ChattyBoi to the AUR
- Make a Windows installer
- (Possibly) CLI mode, either as a parameter or a separate executable.
