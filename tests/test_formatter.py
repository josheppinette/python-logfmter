import logging
import re
import subprocess
import sys
from datetime import datetime

import pytest

from logfmter.formatter import Logfmter

STRING_ESCAPE_RULES = [
    # If the string contains a space, then it must be quoted.
    (" ", '" "'),
    # If the string contains a equals sign, then it must be quoted.
    ("=", '"="'),
    # All double quotes must be escaped.
    ('"', '"\\""'),
    # If the string requires escaping and quoting, then both
    # operations should be performed.
    (' "', '" \\""'),
    # If the string is empty, then it should be left empty.
    ("", ""),
    # If the string contains a newline, then it should be escaped.
    ("\n", "\\n"),
    ("\n\n", "\\n\\n"),
    # If the string contains a backslash and needs to be quoted, then
    # the backslashes need to be escaped.
    ("\\", "\\"),
    ("\\ ", '"\\\\ "'),
    ('\\"', '"\\\\\\""'),
]

TYPE_CONVERSION_RULES = [
    # None values will be converted to an empty string.
    (None, ""),
    # True values will be converted to "true".
    (True, "true"),
    # False values wll be converted to "false".
    (False, "false"),
    # Numbers will be converted to their string representation.
    (1, "1"),
    # Strings will be passed through the `format_string` function.
    ("=", '"="'),
    # Objects will be converted to their string representation using `str`.
    (Exception("="), '"="'),
]


@pytest.mark.parametrize(
    "value,expected",
    STRING_ESCAPE_RULES,
)
def test_format_string(value, expected):
    assert Logfmter.format_string(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    TYPE_CONVERSION_RULES,
)
def test_format_value(value, expected):
    assert Logfmter.format_value(value) == expected


def test_format_exc_info():
    try:
        raise Exception("alpha")
    except Exception:
        exc_info = sys.exc_info()

    value = Logfmter().format_exc_info(exc_info)

    assert value.startswith('"') and value.endswith('"')

    tokens = value.strip('"').split("\\n")

    assert len(tokens) == 4
    assert "Traceback (most recent call last):" in tokens
    assert "Exception: alpha" in tokens


@pytest.mark.parametrize(
    "value,expected",
    [({"a": 1}, "a=1"), ({"a": 1, "b": 2}, "a=1 b=2"), ({"a": " "}, 'a=" "')],
)
def test_format_params(value, expected):
    assert Logfmter.format_params(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("first_name", "first_name"),
        ("first name", "first_name"),
        ("", "_"),
        ("first\nname", "first\\nname"),
    ],
)
def test_normalize_key(value, expected):
    assert Logfmter.normalize_key(value) == expected


@pytest.mark.parametrize(
    "record,expected",
    [({"msg": "test"}, {}), ({"value": 1}, {"value": 1})],
)
def test_get_extra(record, expected):
    # Generate a real `logging.LogRecord` from the provided dictionary.
    record = logging.makeLogRecord(record)

    assert Logfmter.get_extra(record) == expected


@pytest.mark.parametrize(
    "record,expected",
    [
        # When providing a dictionary as the log msg, the msg keys
        # will be used as logfmt parameters.
        ({"levelname": "INFO", "msg": {"a": 1}}, "at=INFO a=1"),
        # When providing extra parameters, they will be combined with
        # msg string in the final logfmt parameters.
        ({"levelname": "INFO", "msg": "test", "a": 1}, "at=INFO msg=test a=1"),
        # All parameter values will be passed through the format pipeline.
        ({"levelname": "INFO", "msg": "="}, 'at=INFO msg="="'),
        # All parameter keys should be normalized.
        (
            {"levelname": "INFO", "msg": {"first name": "josh"}},
            "at=INFO first_name=josh",
        ),
        # Any existing exc_info will be appropriately formatted and
        # added to the log output.
        (
            {
                "levelname": "INFO",
                "msg": "alpha",
                "exc_info": (
                    Exception,
                    Exception("alpha"),
                    None,
                ),  # We don't pass a traceback, because they are difficult to fake.
            },
            'at=INFO msg=alpha exc_info="Exception: alpha"',
        ),
        # If, for some odd reason, someone passes in an empty msg dictionary. It
        # should be properly formatted without extra spaces.
        ({"levelname": "INFO", "msg": {}}, "at=INFO"),
    ],
)
def test_format_default(record, expected):
    # Generate a real `logging.LogRecord` from the provided dictionary.
    record = logging.makeLogRecord(record)

    assert Logfmter().format(record) == expected


@pytest.mark.parametrize(
    "keys,mapping,record,expected",
    [
        # Any provided keys should be included in the final params.
        (
            ["at", "levelno"],
            None,
            {"levelname": "INFO", "levelno": 1, "msg": {"a": 1}},
            "at=INFO levelno=1 a=1",
        ),
        # If a provided key has a mapping and the mapping attribute exists,
        # then that key should be included in the final params.
        (
            ["at", "no"],
            {"at": "levelname", "no": "levelno"},
            {"levelname": "INFO", "levelno": 1, "msg": {"a": 1}},
            "at=INFO no=1 a=1",
        ),
        # If a provided key has a mapping and the mapping attribute does not exist,
        # then that key should not be included in the final params.
        (
            ["at", "dne"],
            {"at": "levelname", "dne": "?"},
            {"levelname": "INFO", "msg": {"a": 1}},
            "at=INFO a=1",
        ),
        # A user should be able to specify no default keys.
        (
            [],
            None,
            {"msg": {"a": 1}},
            "a=1",
        ),
        # Any provided keys, along with their mappings, should be normalized.
        (
            ["log level"],
            {"log level": "levelname"},
            {"levelname": "INFO", "msg": {"a": 1}},
            "log_level=INFO a=1",
        ),
    ],
)
def test_format_provided_keys(keys, mapping, record, expected):
    """
    If someone requests an additional default key be added to the log output,
    then it should be added as a parameter. Any provided mapping should also
    be utilized.
    """

    # Generate a real `logging.LogRecord` from the provided dictionary.
    record = logging.makeLogRecord(record)

    if mapping:
        formatter = Logfmter(keys=keys, mapping=mapping)
    else:
        formatter = Logfmter(keys=keys)

    assert formatter.format(record) == expected


def test_format_asctime():
    """
    If a user requests asctime in the default keys, then it should be rendered
    in the final log output.
    """
    # Generate a real `logging.LogRecord` from the provided dictionary.
    record = logging.makeLogRecord({"msg": "alpha"})

    value = Logfmter(keys=["asctime"]).format(record)

    asctime = re.search(r'asctime="(.*)"', value).group(1)
    asctime_without_msecs = asctime.split(",")[0]
    datetime.strptime(asctime_without_msecs, "%Y-%m-%d %H:%M:%S")


def test_format_asctime_mapping():
    """
    If a user requests asctime in the default keys through a mapping, then it should be
    rendered in the final log output.
    """
    # Generate a real `logging.LogRecord` from the provided dictionary.
    record = logging.makeLogRecord({"msg": "alpha"})

    value = Logfmter(keys=["when"], mapping={"when": "asctime"}).format(record)

    asctime = re.search(r'when="(.*)"', value).group(1)
    asctime_without_msecs = asctime.split(",")[0]
    datetime.strptime(asctime_without_msecs, "%Y-%m-%d %H:%M:%S")


def test_format_datefmt():
    """
    If a user requests asctime and provided a datefmt, then that datefmt will be used to
    format the asctime.
    """
    # Generate a real `logging.LogRecord` from the provided dictionary.
    record = logging.makeLogRecord({"msg": "alpha"})

    value = Logfmter(keys=["asctime"], datefmt=" %H ").format(record)

    asctime = re.search(r'asctime="(.*)"', value).group(1)
    datetime.strptime(asctime, " %H ")


@pytest.mark.parametrize(
    "record",
    [
        {"msg": "alpha", "levelname": "INFO"},
        {"msg": {"msg": "alpha"}, "levelname": "INFO"},
    ],
)
def test_extra_keys(record):
    """
    When attributes are added directly to the `logging.LogRecord` object, they should
    be included in the output and not be duplicated, regardless of a str or dict based
    msg object.
    """
    record = logging.makeLogRecord(record)
    record.attr = "value"

    assert (
        Logfmter(keys=["at", "attr"]).format(record) == "at=INFO msg=alpha attr=value"
    )


@pytest.mark.external
@pytest.mark.parametrize(
    "value",
    [x[0] for x in TYPE_CONVERSION_RULES + STRING_ESCAPE_RULES],
)
def test_external_tools_compatibility(value):
    """
    Verify that the logfmt output can be parsed and identically
    reformatted by external tools.
    """
    record = logging.makeLogRecord({"msg": {"foo": value}, "levelname": "INFO"})

    formatted = Logfmter(keys=["at"]).format(record)

    result = subprocess.run(
        ["golang-logfmt-echo"],
        input=formatted,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, formatted
    assert len(result.stdout.splitlines()) == 1, formatted
    assert result.stdout.splitlines()[0] == formatted
