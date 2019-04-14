Configuration reference
=======================

.. contents::

Omnibot uses the `UCL <https://github.com/vstakhov/libucl>`_ file format for its configuration.

Root objects
------------

Right now, there is exactly one root object: ``server``. This is to leave space for new
configuration options in the future.

Server objects
--------------

The root ``server`` object contains key-value pairs of IRC server names (or addresses) mapping to
objects describing how to connect to the server. For example::

    server "irc.example.com" {
        # server configuration goes here
    }

    server "freenode" {
        address = "chat.freenode.net"
        # additional configuration
    }

Inside of server blocks, the following values can be set.

* ``address``
    * **Type**: String
    * **Description**: The address of the server to connect to.
    * **Default**: The key of the server object itself. In the first example, ``"irc.example.com"`` is
      used.
* ``port``
    * **Type**: Int
    * **Description**: The port of the server to connect to.
    * **Default**: 6697 if ``ssl`` is ``true``, else 6667.
* ``ssl``
    * **Type**: Bool
    * **Description**: Whether to connect using SSL or not.
    * **Default**: ``false``
* ``nick``
    * **Type**: String
    * **Description**: The nickname to use on this server.
    * **Default**: \*Required.
* ``data``
    * **Type**: String
    * **Description**: The directory to store module data for this server in.
    * **Default**: ``./data``
* ``modules``
    * **Type**: Object
    * **Description**: An object of module configurations for the server to load (see below).
    * **Default**: ``{}`` (empty object)


Examples
^^^^^^^^

TODO 

Module objects
--------------

The ``modules`` server object value is how Omnibot gets its functionality. A number of modules are
supplied with omnibot - check the :doc:`module reference <module_ref>` for details. Configured
modules are only ever reloaded if their configuration changes - otherwise, the module's
configuration remains unchanged.


* ``channels``
    * **Type**: Array
    * **Description**: The channels that this module will be active on.
    * **Default**: ``[]`` (empty array)
* ``always_reload``
    * **Type**: Bool
    * **Description**: Whether to reload this module every time configuration is reloaded (``true``),
                     or to only reload when this module's configuration is changed (``false``).
    * **Default**: ``false``
* ``data``
    * **Type**: String
    * **Description**: The data directory to store this module's data in, if any.
    * **Default**: The name of the module.
* ``args``
    * **Type**: Object
    * **Description**: Named arguments that this module can use to modify its behavior. Check the
                     module's documentation for more inforation.
    * **Default**: ``{}`` (empty object)


Examples
^^^^^^^^

TODO 
