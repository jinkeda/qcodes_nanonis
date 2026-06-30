"""Full scan workflow (planned).

The useful sequence from ``doScan``: position at the correct corner, configure
frame/buffer/speed, start, wait, validate timeout, and return the saved file or
dataset, with snapshot/restore and stop-and-wait recovery matching the bias
spectroscopy contract.

Not yet implemented; the likely next vertical. See ``reports/blueprint.md``
(Next milestone) and ``reports/workflow_layer_walkthrough.md`` (M4) for scope.
"""
