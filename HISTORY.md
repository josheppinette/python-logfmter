# 0.0.12 (2026-3-11)

- Improve handling of invisible control characters
- Drop support for Python 3.9
- Add support for Python 3.14
- Update development dependencies
- Improve tests
- Improve ci/cd performance

# 0.0.11 (2025-10-13)

- Fix control character escaping
- Fix newline escaping
- Add support for ignored_keys
- Improve performance by using cached variables
- Update formatter to format stack_info if available
- Add support for format-able default values
- Resolve test warnings
- Improve external test harness
- Update format/lint tooling

# 0.0.10 (2025-07-30)

- Improve support for logging dicts via flattened keys
- Add test system to verify log parsing by third party tools
- Add proper escaping of backslashes to fix log consumption by third party
tools
- Refactor traceback generation
- Improve documentation

# 0.0.9 (2025-01-23)

- Resolve pyright lint issue
- Remove official support for eol python versions
- Add nix dev support
- Improve documentation
- Add official Python 3.13 support

# 0.0.8 (2024-05-24)

- Add official support for Python 3.12.

# 0.0.7 (2024-01-23)

- Improve documentation
- Add support for default key/value pairs provided via log record factory.
- Fix duplication issue that happened when keys/extras/msg values overlapped.

# 0.0.6 (2022-04-22)

- Improve documentation.
- Normalize keys to prevent users from breaking the logfmt style.

# 0.0.5 (2022-04-20)

- Add support for include native log record attributes in the final log output.
- Add support for overriding the date format used when formatting the `asctime` attribute.

# 0.0.4 (2022-03-29)

- Fix the usage documentation
- Escape newline characters in all logged values. Previously, you could generate
  multi-line log statements. This should never be the case.
- Add support for auto-generating `exc_info` parameters. If the log record is
  generated with `exc_info`, as in when using `logging.exception(...)`, the
  log message will contain properly formatted exception and traceback information.
- Add support for logging with an empty message dictionary.

# 0.0.3 (2022-01-13)

- Include type hints

# 0.0.1 (2022-01-06)

- Incept
