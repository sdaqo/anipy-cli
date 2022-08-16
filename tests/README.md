# Setup
```
pip install pytest
```
Tests only run under linux

# Run the Tests:

```
$ python runtests.py
```
### Options
 ```
$ python runtests.py --help
```
Get documentation for pytest [here](https://docs.pytest.org).

#### Example
```
Exclude tests that are very slow.
$ python runtests.py -m "not veryslow"
```
