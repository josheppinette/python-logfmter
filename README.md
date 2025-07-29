![python logfmter](./banner.png)

<div align="center">

[![pre-commit](https://github.com/josheppinette/python-logfmter/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/josheppinette/python-logfmter/actions/workflows/pre-commit.yml)
[![test](https://github.com/josheppinette/python-logfmter/actions/workflows/test.yml/badge.svg)](https://github.com/josheppinette/python-logfmter/actions/workflows/test.yml)
[![python-3.9-3.10-3.11-3.12-3.13](https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11|%203.12|%203.13-blue.svg)](.github/workflows/test.yml)

Add [logfmt](https://www.brandur.org/logfmt) structured logging using the stdlib logging module and without changing a single log call.

</div>

```python
> logging.warn("user created", extra=user)

at=WARNING msg="user created" first_name=John last_name=Doe age=25
```

# Table of Contents

1. [Why](#why)
2. [Install](#install)
3. [Usage](#usage)
   1. [Integration](#integration)
   2. [Configuration](#configuration)
   3. [Extension](#extension)
   4. [Guides](#guides)
4. [Development](#development)
   1. [Required Software](#required-software)
   2. [Getting Started](#getting-started)
   3. [Publishing](#publishing)

# Why

- enables both human and computer readable logs, [recommended as a "best practice" by Splunk](https://dev.splunk.com/enterprise/docs/developapps/addsupport/logging/loggingbestpractices/)
- formats all first and third party logs, you never have to worry about a library using a different logging format
- simple to integrate into any existing application, requires no changes to existing log statements i.e. [structlog](https://github.com/hynek/structlog)

# Install

```sh
$ pip install logfmter
```

# Usage

This package exposes a single `Logfmter` class that can be integrated into
the [standard library logging system](https://docs.python.org/3/howto/logging.html) like any [`logging.Formatter`](https://docs.python.org/3/howto/logging.html#formatters).

## Integration

**[basicConfig](https://docs.python.org/3/library/logging.html#logging.basicConfig)**

```python
import logging
from logfmter import Logfmter

handler = logging.StreamHandler()
handler.setFormatter(Logfmter())

logging.basicConfig(handlers=[handler])

logging.error("hello", extra={"alpha": 1}) # at=ERROR msg=hello alpha=1
logging.error({"token": "Hello, World!"}) # at=ERROR token="Hello, World!"
```

**[dictConfig](https://docs.python.org/3/library/logging.config.html#logging.config.dictConfig)**

_If you are using `dictConfig`, you need to consider your setting
of `disable_existing_loggers`. It is enabled by default, and causes
any third party module loggers to be disabled._

```python
import logging.config

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "logfmt": {
                "()": "logfmter.Logfmter",
            }
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "logfmt"}
        },
        "loggers": {"": {"handlers": ["console"], "level": "INFO"}},
    }
)

logging.info("hello", extra={"alpha": 1}) # at=INFO msg=hello alpha=1
```

_Notice, you can configure the `Logfmter` by providing keyword arguments as dictionary
items after `"()"`:_

```python
...

    "logfmt": {
        "()": "logfmter.Logfmter",
        "keys": [...],
        "mapping": {...}
    }

...
```

**[fileConfig](https://docs.python.org/3/library/logging.config.html#logging.config.fileConfig)**

Using logfmter via fileConfig is not supported, because fileConfig does not support custom formatter initialization. There may be some hacks to make this work in the future. Let me know if you have ideas or really need this.

## Configuration

**keys**

By default, the `at=<levelname>` key/value will be included in all log messages. These
default keys can be overridden using the `keys` parameter. If the key you want to include
in your output is represented by a different attribute on the log record, then you can
use the `mapping` parameter to provide that key/attribute mapping.

Reference the Python [`logging.LogRecord` Documentation](https://docs.python.org/3/library/logging.html?highlight=logrecord#logging.LogRecord)
for a list of available attributes.

```python
import logging
from logfmter import Logfmter

formatter = Logfmter(keys=["at", "processName"])

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logging.basicConfig(handlers=[handler])

logging.error("hello") # at=ERROR processName=MainProceess msg=hello
```

**mapping**

By default, a mapping of `{"at": "levelname"}` is used to allow the `at` key to reference
the log record's `levelname` attribute. You can override this parameter to provide your
own mappings.

```python
import logging
from logfmter import Logfmter

formatter = Logfmter(
    keys=["at", "process"],
    mapping={"at": "levelname", "process": "processName"}
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logging.basicConfig(handlers=[handler])

logging.error("hello") # at=ERROR process=MainProceess msg=hello
```

**datefmt**

If you request the `asctime` attribute (directly or through a mapping), then the date format
can be overridden through the `datefmt` parameter.

```python
import logging
from logfmter import Logfmter

formatter = Logfmter(
    keys=["at", "when"],
    mapping={"at": "levelname", "when": "asctime"},
    datefmt="%Y-%m-%d"
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logging.basicConfig(handlers=[handler])

logging.error("hello") # at=ERROR when=2022-04-20 msg=hello
```

## Extension

You can subclass the formatter to change its behavior.

```python
import logging
from logfmter import Logfmter


class CustomLogfmter(Logfmter):
    """
    Provide a custom logfmt formatter which formats
    booleans as "yes" or "no" strings.
    """

    @classmethod
    def format_value(cls, value):
        if isinstance(value, bool):
            return "yes" if value else "no"

	return super().format_value(value)

handler = logging.StreamHandler()
handler.setFormatter(CustomLogfmter())

logging.basicConfig(handlers=[handler])

logging.error({"example": True}) # at=ERROR example=yes
```

## Guides

**Default Key/Value Pairs**

Instead of providing key/value pairs at each log call, you can override
the log record factory to provide defaults:

```py
_record_factory = logging.getLogRecordFactory()

def record_factory(*args, **kwargs):
    record = _record_factory(*args, **kwargs)
    record.trace_id = 123
    return record

logging.setLogRecordFactory(record_factory)
```

This will cause all logs to have the `trace_id=123` pair regardless of including
`trace_id` in keys or manually adding `trace_id` to the `extra` parameter or the `msg` object.

# Development

## Required Software

If you are using [nix](https://zero-to-nix.com/start/install/) & [direnv](https://direnv.net/docs/installation.html), then your dev environment will be managed automatically. Otherwise, you will need to manually install the following software:

- [direnv](https://direnv.net)
- [git](https://git-scm.com/)
- [pyenv](https://github.com/pyenv/pyenv#installation)

> Additionally, if you aren't using nix, then you will need to manually build
> the "external" tools found in `external`. These are used during testing to
> verify compatibility with libraries from different ecosystems. Alternatively, you can exclude those tests with `pytest -m "not external"`, but this is not recommended.

## Getting Started

**Setup**

> If you are using pyenv, you will need to install the correct versions of python using `<runtimes.txt xargs -n 1 pyenv install -s`.

```sh
$ direnv allow
$ pip install -r requirements/dev.txt
$ pre-commit install
$ pip install -e .
```

**Tests**

_Run the test suite against the active python environment._

```sh
$ pytest
```

_Run the test suite against the active python environment and
watch the codebase for any changes._

```sh
$ ptw
```

_Run the test suite against all supported python versions._

```sh
$ tox
```

## Contributing

1. Create an issue with all necessary details.
2. Create a branch off from `main`.
3. Make changes.
4. Verify tests pass in all supported python versions: `tox`.
5. Verify code conventions are maintained: `git add --all && pre-commit run -a`.
6. Create your commit following the [conventionalcommits](https://www.conventionalcommits.org/en/v1.0.0/#summary).
7. Create a pull request with all necessary details: description, testing notes, resolved issues.

## Publishing

**Create**

1. Update the version number in `logfmter/__init__.py`.

2. Add an entry in `HISTORY.md`.

3. Commit the changes, tag the commit, and push the tags:

   ```sh
   $ git commit -am "v<major>.<minor>.<patch>"
   $ git tag v<major>.<minor>.<patch>
   $ git push origin main --tags
   ```

4. Convert the tag to a release in GitHub with the history
   entry as the description.

**Build**

```sh
$ python -m build
```

**Upload**

```
$ twine upload dist/*
```
