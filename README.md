# HeartBeats

A Garmin's SDK application for smart watch Fenix 5x+, probably compatible and with others, but untested. It starts to log heart intervals, in milliseconds, as soon as it starts. It shows the seconds passed and the amount of records collected so far. 

Includes a parsing/ python to extract a JSON (full) and CSV (just the heart beat intervals). When
ran, that file parses all `*.fit` files in its directory.

## Requirements

* Download the latest Garmin SDK manager: https://developer.garmin.com/connect-iq/sdk/
* Run that wxWidgets (saw the stack dump) wizard and install something like API 3.3+ and whatever the
  device is the goal.
* Install Java (portable!) https://github.com/Vinetos/java-portable
* Install VSCode (eeewww!) https://code.visualstudio.com/docs/editor/portable
* In VSCode install the Monkey C extension (and Vim!)

The API and Device must be configured for whatever is the watch.

## Requirements Python

Need to `pip install pytz tzlocal garmin_fit_sdk`.

## References
https://developer.garmin.com/connect-iq/overview/
https://developer.garmin.com/connect-iq/api-docs/index.html
