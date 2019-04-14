# omnibot

Omnibot is an IRC chatbot framework. It is designed for:

* Ease of module and command creation.
* Uptime: module code and configuration can be reloaded on demand.

This project is presently in development. Please report bugs through the
[Github issues](https://github.com/alekratz/omnibot/issues) page as you encounter them.

# TODO

There are a few TODOs that I have queued in my head. Feel free to suggest features via the
aforementioned issues page.

* More shortcuts to do common things (e.g. required config for modules)
* Data directory for modules, specified in config
* Expand past IRC and support other chat platforms
    * Discord
    * Slack
    * Zulip
    * Gitter?
    * Google Chat?
    * anything else?
* Example config
* Install instructions
* Development documentation
* More bots
    * Acro bot
    * Unit conversion bot
* Move 'modules' directory to someplace inside of 'omnibot', and name it something like
  'omnibot.contrib' like Django does
* Do module imports using the python import system so external modules can be used as packages,
  instead of looking for local `.py` files
