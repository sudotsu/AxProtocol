Logging Configuration
=====================

Purpose
- Centralize log levels, formatting, and rotation without code changes.

File
- Path: config/logging.yaml

Schema (dictConfig)
- version: 1
- formatters: named formatters (e.g., standard, terse)
- handlers: console and rotating file handlers
- loggers: module-specific loggers (e.g., axprotocol)
- root: default level and handlers

Example (excerpt)
version: 1
formatters:
  standard:
    format: "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: standard
    filename: logs/axp.log
    maxBytes: 1048576
    backupCount: 5
loggers:
  axprotocol:
    level: INFO
    handlers: [console, file]
    propagate: false

Usage
- Load via logging.config.dictConfig(yaml.safe_load(...)).
- Default root level is WARNING; set module loggers to INFO for operational visibility.

Operational Notes
- Ensure logs/ exists or handler creates it.
- Rotate at 1 MB with 5 backups by default.

