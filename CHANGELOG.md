# Changelog

All notable changes to this project are documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/);
each section corresponds to a git version tag (which is also the release
published to PyPI). Entries are commit subjects and PR titles, verbatim.

## [0.1.3] - 2026-06-13

- test: make record-shape assertions robust to chromadb version drift
- Modernize type annotations (PEP 585/604) + lazy annotations
- ci: migrate old CI to uv (wads-migrate setup-to-pyproject + ci-to-uv); drop legacy setup.cfg/setup.py
- edit setup

### Added

- feat: Enhance data loaders and utility functions; add MappingLoader class and improve vectorization
- feat: max_workers=None defaults to num of cpus

## [0.1.2] - 2024-01-03

### Added

- feat: endow vectorize with concurrency

## [0.1.1] - 2024-01-03

### Added

- feat: FileLoader

### Fixed

- fix: doctests

## [0.1.0] - 2024-01-03

- first commit

### Added

- feat: Actual code

### Fixed

- fix: doctest
- fix: doctests
- fix: ci
