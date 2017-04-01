=======================
Zipline Poloniex Bundle
=======================

Poloniex Data Bundle providing for zipline_, the Pythonic algorithmic trading library.


Description
===========

Just install the data bundle with pip::

    pip install zipline-poloniex

and create a file ``$HOME/.zipline/extension.py`` calling zipline's register_ function.
The ``create_bundle`` function returns the necessary ingest function for ``register``.
Use the ``Pairs`` record for common US-Dollar to crypto-currency pairs.


Example
=======

Content of ``$HOME/.zipline/extension.py``:

.. code:: python

    import pandas as pd
    from zipline_poloniex import create_bundle, Pairs, register

    register(
        'poloniex_eth_2016',
        create_bundle(
            [Pairs.usdt_eth],
            pd.Timestamp('2016-01-01', tz='utc'),
            pd.Timestamp('2016-12-31', tz='utc'),
        ),
        calendar_name='POLONIEX',
        minutes_per_day=24*60
    )


Note
====

This project has been set up using PyScaffold 2.5.7. For details and usage
information on PyScaffold see http://pyscaffold.readthedocs.org/.

.. _register: http://www.zipline.io/appendix.html?highlight=register#zipline.data.bundles.register
.. _zipline: http://www.zipline.io/