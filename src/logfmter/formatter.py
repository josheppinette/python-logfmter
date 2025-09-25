import logging
import numbers
from types import TracebackType
from typing import Any, Dict, List, Optional, Tuple, Type, cast

ExcInfo = Tuple[Type[BaseException], BaseException, TracebackType]

# Reserved log record attributes cannot be overwritten. They
# will not be included in the formatted log.
#
# https://docs.python.org/3/library/logging.html#logrecord-attributes
RESERVED: Tuple[str, ...] = (
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
)

QUOTE_CHARS = str.maketrans(
    "", "", " =" + "".join(chr(c) for c in list(range(0x20)) + [0x7F])
)
REPLACEMENTS = {chr(c): f"\\u{c:04x}" for c in list(range(0x20)) + [0x7F]}
REPLACEMENTS.update({"\n": "\\n", "\t": "\\t", "\r": "\\r"})


class _DefaultFormatter(logging.Formatter):
    def format(self, record):
        exc_info = record.exc_info
        exc_text = record.exc_text
        stack_info = record.stack_info
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        try:
            return super().format(record)
        finally:
            record.exc_info = exc_info
            record.exc_text = exc_text
            record.stack_info = stack_info


class Logfmter(logging.Formatter):
    @classmethod
    def format_string(cls, value: str) -> str:
        """
        Process the provided string with any necessary quoting and/or escaping.
        """
        needs_dquote_escaping = '"' in value
        needs_quoting = needs_dquote_escaping or value.translate(QUOTE_CHARS) != value
        needs_backslash_escaping = "\\" in value and needs_quoting

        if needs_backslash_escaping:
            value = value.replace("\\", "\\\\")

        if needs_dquote_escaping:
            value = value.replace('"', '\\"')

        for char, replacement in REPLACEMENTS.items():
            value = value.replace(char, replacement)

        if needs_quoting:
            value = '"{}"'.format(value)

        return value if value else ""

    @classmethod
    def format_value(cls, value) -> str:
        """
        Map the provided value to the proper logfmt formatted string.
        """
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, numbers.Number):
            return str(value)

        return cls.format_string(str(value))

    @classmethod
    def format_params(cls, params: dict) -> str:
        """
        Return a string representing the logfmt formatted parameters.
        """
        return " ".join(
            [
                "{}={}".format(key, cls.format_value(value))
                for key, value in params.items()
            ]
        )

    @classmethod
    def normalize_key(cls, key: str) -> str:
        """
        Return a string whereby any spaces are converted to underscores and
        newlines are escaped.

        If the provided key is empty, then return a single underscore. This
        function is used to prevent any logfmt parameters from having invalid keys.

        As a choice of implementation, we normalize any keys instead of raising an
        exception to prevent raising exceptions during logging. The goal is to never
        impede logging. This is especially important when logging in exception handlers.
        """
        if not key:
            return "_"

        return key.replace(" ", "_").replace("\n", "\\n")

    @classmethod
    def get_extra(cls, record: logging.LogRecord) -> dict:
        """
        Return a dictionary of logger extra parameters by filtering any reserved keys.
        """
        extras = {}

        for key, value in record.__dict__.items():
            key = cls.normalize_key(key)

            if key in RESERVED:
                continue

            if isinstance(value, dict):
                extras.update(cls.flatten_dict(value, key))
            else:
                extras[key] = value

        return extras

    @classmethod
    def flatten_dict(cls, v: dict, root: str = "") -> dict[str, Any]:
        """
        Return a dictionary whereby the input dictionary is converted to
        depth equal to one with keys that are joined via periods.
        """
        flattened = {}

        for key, value in v.items():
            key = f"{root}.{cls.normalize_key(key)}" if root else cls.normalize_key(key)

            if isinstance(value, dict):
                flattened.update(cls.flatten_dict(value, key))
            else:
                flattened[key] = value

        return flattened

    def __init__(
        self,
        keys: List[str] = ["at"],
        mapping: Dict[str, str] = {"at": "levelname"},
        datefmt: Optional[str] = None,
        defaults: Optional[Dict[str, str]] = None,
        ignored_keys: Optional[List[str]] = None,
    ):
        super().__init__("%(message)s", datefmt)
        self.keys = [self.normalize_key(key) for key in keys]
        self.mapping = {
            self.normalize_key(key): value for key, value in mapping.items()
        }
        self.defaults = {
            key: _DefaultFormatter(value, style="{")
            for key, value in (defaults or {}).items()
        }
        self.ignored_keys = ignored_keys or []

    def format(self, record: logging.LogRecord) -> str:
        # If the 'asctime' attribute will be used, then generate it.
        if not hasattr(record, "asctime"):
            if "asctime" in self.keys or "asctime" in self.mapping.values():
                record.asctime = self.formatTime(record, self.datefmt)

        if isinstance(record.msg, dict):
            params = self.flatten_dict(record.msg)
        else:
            params = {"msg": record.getMessage()}

        params.update(self.get_extra(record))

        tokens = []

        # Add the initial tokens from the provided list of default keys.
        #
        # This supports parameters which should be included in every log message. The
        # values for these keys must already exist on the log record. If they are
        # available under a different attribute name, then the formatter's mapping will
        # be used to lookup these attributes. e.g. 'at' from 'levelname'
        for key in self.keys:
            attribute = key

            # If there is a mapping for this key's attribute, then use it to lookup
            # the key's value.
            if key in self.mapping:
                attribute = self.mapping[key]

            # If this key is in params, then skip it, because it was manually passed in
            # will be added via the params system.
            if attribute in params:
                continue

            if hasattr(record, attribute):
                value = getattr(record, attribute)
            elif attribute in self.defaults:
                value = self.defaults[attribute].format(record)
            else:
                continue

            if isinstance(value, dict):
                continue

            tokens.append("{}={}".format(key, self.format_value(value)))

        formatted_params = self.format_params(
            {
                k: v
                for k, v in params.items()
                if k not in self.ignored_keys
                and k.split(".", 1)[0] not in self.ignored_keys
            }
        )
        if formatted_params:
            tokens.append(formatted_params)

        if (
            record.exc_info
            and not record.exc_text
            and "exc_info" not in self.ignored_keys
        ):
            # Cast exc_info to its not null variant to make mypy happy.
            exc_info = cast(ExcInfo, record.exc_info)
            record.exc_text = self.formatException(exc_info)

        if record.exc_text and "exc_info" not in self.ignored_keys:
            tokens.append(f"exc_info={self.format_string(record.exc_text)}")

        if record.stack_info and "stack_info" not in self.ignored_keys:
            stack_info = self.formatStack(record.stack_info).rstrip("\n")
            tokens.append(f"stack_info={self.format_string(stack_info)}")

        return " ".join(tokens)
