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

   
+---------------+------------------------------------------+--------+------------------------------+
| Name          | Description                              | Type   | Default                      |
+===============+==========================================+========+==============================+
| ``address``   | The address of the server to connect to. | String | The key of the server object |
|               |                                          |        | itself. In the first example,|
|               |                                          |        | "irc.example.com" is used.   |
+---------------+------------------------------------------+--------+------------------------------+
| ``port``      | The port of the server to connect on.    | Int    | 6667 if ``ssl`` is false,    |
|               |                                          |        | otherwise 6697.              |
+---------------+------------------------------------------+--------+------------------------------+
| ``ssl``       | Whether to connect using SSL or not.     | Bool   | ``false``                    |
+---------------+------------------------------------------+--------+------------------------------+
| ``nick``      | The nickname to use.                     | String | \*Required.                  |
+---------------+------------------------------------------+--------+------------------------------+
| ``data``      | The directory to store module data in.   | String | ``./data``                   |
+---------------+------------------------------------------+--------+------------------------------+
| ``modules``   | An object of module configurations for   | Object | ``{}`` (empty object)        |
|               | the server to load (see below).          |        |                              |
+---------------+------------------------------------------+--------+------------------------------+


Examples
^^^^^^^^

TODO 

Module objects
--------------

The ``modules`` server object value is how Omnibot gets its functionality. A number of modules are
supplied with omnibot - check the :doc:`module reference <module_ref>` for details. Configured
modules are only ever reloaded if their configuration changes - otherwise, the module's
configuration remains unchanged.


+-------------------+------------------------------------------+--------+--------------------------+
| Name              | Description                              | Type   | Default                  |
+===================+==========================================+========+==========================+
| ``channels``      | The channels that this module will be    | Array  | ``[]`` (empty array)     |
|                   | active on.                               |        |                          |
+-------------------+------------------------------------------+--------+--------------------------+
| ``always_reload`` | This causes the module to be reloaded    | Bool   | false                    |
|                   | every time configuration is reloaded,    |        |                          |
|                   | not just when the configuration changes. |        |                          |
+-------------------+------------------------------------------+--------+--------------------------+
| ``data``          | The directory to store this module's     | String | The name of the module.  |
|                   | data in, if any.                         |        |                          |
+-------------------+------------------------------------------+--------+--------------------------+
| ``args``          | Named arguments that this module can use | Object | ``{}`` (empty object)    |
|                   | to modify its behavior.                  |        |                          |
+-------------------+------------------------------------------+--------+--------------------------+


Examples
^^^^^^^^

TODO 
