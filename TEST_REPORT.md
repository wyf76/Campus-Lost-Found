# Backend Test Report

Date: 2026-10-26

## Test setup

- Framework: Django `TestCase`, built on Python's `unittest` framework.
- Command: `python manage.py test items chat`
- Scope: reports and chat apps.
- Database: Django created and removed an isolated PostgreSQL test database.

## Result

**PASS — 35 tests across 7 test classes.**

All tests passed in 5.742 seconds. Django's system check reported no issues.

## Coverage

- Report form and model behavior, including valid data, required fields, choice/date validation, title length boundaries, default resolution state, timestamps, author relation, and optional images.
- Report API behavior, including authentication, server-assigned authorship, malformed shapes, `None` and wrong JSON types, a 1,000-entry JSON array, title length boundaries, search, filters, and details.
- Message form and model behavior, including whitespace handling, `None` and non-string inputs, 4,000-character boundary, relationships, timestamps, and duplicate conversation prevention.
- Chat API behavior, including authentication, conversation reuse, self-chat prevention, message sender identity, invalid message bodies, and participant-only access.
