API Reference
=============

Core Modules
------------

.. automodule:: nanonis.command
   :members:

.. automodule:: nanonis.protocol
   :members:

QCoDeS Integration
------------------

.. autoclass:: nanonis.qcodes.instrument.NanonisInstrument
   :members:

.. autoclass:: nanonis.qcodes.channels.bias.BiasChannel
   :members:

.. autoclass:: nanonis.qcodes.channels.scan.ScanChannel

.. automethod:: nanonis.qcodes.channels.scan.ScanChannel.set_frame
.. automethod:: nanonis.qcodes.channels.scan.ScanChannel.start
.. automethod:: nanonis.qcodes.channels.scan.ScanChannel.stop
.. automethod:: nanonis.qcodes.channels.scan.ScanChannel.pause
.. automethod:: nanonis.qcodes.channels.scan.ScanChannel.resume
