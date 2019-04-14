Quickstart
==========

.. toctree::
    :maxdepth: 2
    :caption: Contents:


Requirements
------------

The only hard requirement to get Omnibot running is Python 3.5 (or newer), and Pip.

Omnibot attempts to support Python 3.5 and greater. There may be a handful of modules which may
require a more recent version. Consult the module's documentation if you are unsure.

Installation
------------

Via Pip
^^^^^^^

Omnibot is available on the Python Package index as ``omnibot``. You can install it with Pip, using
``pip install omnibot``. If you are running in a POSIX-like environment, you can run ``which
omnibot`` to enusre that the program was installed correctly.

From source
^^^^^^^^^^^

#. | Clone the Git repository and enter the directory.
   | ``git clone https://github.com/alekratz/omnibot && cd omnibot``
#. | Install dependencies.
   | ``pip install -r requirements.txt``

Omnibot should be Ready to Roll.

Configuring
-----------

Configuration is one of the most important parts of Omnibot. If you installed from source, there is
already an ``omnibot.example.ucl`` configuration present -- copy that to ``omnibot.ucl`` with ``cp
omnibot.example.ucl omnibot.ucl``. If you installed from Pip, an example configuration file is
provided below::
    
    # Connect to an example server

    server "irc.example.com" {
        # If you don't supply "address", the name for this server is used instead
        #address = "irc.example.com"
        #

        # If you do not specify a port, it is implied through the `ssl` setting
        # below.  However, the `ssl` setting is *not* implied through the port
        # setting - it is set to `false` unless you explicitly state otherwise.
        #
        # port = 6697
        
        # Whether to use SSL or not.
        ssl = true

        # The nickname to use for this bot.
        nick = "omnibot"

        # Modules to load for this server.
        modules {
            # Nickserv is provided as a built-in module.
            #
            # NOTE: these have only been tested with Anope.
            #
            # A module uses the key "args" for its own configuration.
            nickserv args {
                password = "secret"
                email = "omnibot@omni.bot"
            }

            # A "roll-the-dice" bot. Lets you roll dice in the form of !rtd [X]dY,
            # where X is an optional number of dice, and Y is a number of sides.
            #
            # Additionally provides a !d20 [check] bot to roll for a D20 check.
            rtd {
                channels = ["#idleville"]
            }

            # A bot that gives you a 4chan-style fortune when you use !fortune.
            fortune {
                channels = ["#idleville"]
                always_reload = true
            }

            # A module that will attempt to parse things that look like URLs and give their HTML titles
            # back.
            linkbot {
                channels = ["#idleville"]
            }

            # A fun game where points are awarded for the most words said from a randomly selected list
            # every few hours.
            wordbot {
                channels = ["idleville"]
                always_reload = true
                args {
                    words_per_hour = 60
                    hours_per_round = 5
                }
            }
        }
    }

For a full list of configuration values, be sure to check the :doc:`configuration reference
<config_ref>`.

Omnibot uses the `UCL <https://github.com/vstakhov/libucl>`_ file format for its configuration. If
you are familiar with JSON but not UCL, this is the exact same JSON object as above::

    {
        "server": {
            "irc.example.com": {
                "ssl": true,
                "nick": "omnibot",
                "modules": {
                    "nickserv": {
                        "args": {
                            "password": "secret",
                            "email": "omnibot@omni.bot"
                        }
                    },
                    "rtd": {
                        "channels": [
                            "#idleville"
                        ]
                    },
                    "fortune": {
                        "channels": [
                            "#idleville"
                        ],
                        "always_reload": true
                    },
                    "linkbot": {
                        "channels": [
                            "#idleville"
                        ]
                    },
                    "wordbot": {
                        "channels": [
                            "idleville"
                        ],
                        "always_reload": true,
                        "args": {
                            "words_per_hour": 60,
                            "hours_per_round": 5
                        }
                    }
                }
            }
        }
    }

Running
-------
