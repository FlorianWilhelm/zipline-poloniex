================
zipline-poloniex
================


Add a short description here!


Description
===========


``~/.zipline/extension.py``

.. code:: python

    import pandas as pd

    from zipline.data.bundles import register
    from zipline_poloniex.bundle import create_bundle, Pairs

    register(
        'poloniex',
        create_bundle(
            (
                [Pairs.usdt_eth]
            ),
            pd.Timestamp('2017-01-01', tz='utc'),
            pd.Timestamp('2017-01-02', tz='utc'),
        ),
    )


Note
====

This project has been set up using PyScaffold 2.5.7. For details and usage
information on PyScaffold see http://pyscaffold.readthedocs.org/.
