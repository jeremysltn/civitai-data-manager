# Changelog

All notable changes to this project will be documented in this file. 

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.6.3] - 2025-02-16
### Chore
- Migrate project to Poetry for dependency management.

## [1.6.2] - 2025-02-16
### Refactor
- Centralize version management in package root.

## [1.6.1] - 2025-02-16
### Fix
- Update `sanitize_filename` for new project structure.

## [1.6.0] - 2025-02-16
### Refactor
- Reorganize project structure to follow Python conventions.

## [1.5.5] - 2025-02-09
### Fix
- Handle `None` values in global summary generation.

## [1.5.4] - 2024-12-30
### Feature
- Persist sort preference in `localStorage`.

## [1.5.3] - 2024-12-30
### Feature
- Add file size display and sorting.

## [1.5.2] - 2024-12-30
### Feature
- Add migration script for filename sanitization (fix breaking changes from v1.5.0).

## [1.5.1] - 2024-12-26
### Feature
- Add sorting options to browser page.

## [1.5.0] - 2024-12-26
### Fix
- Improve filename handling.

## [1.4.4] - 2024-12-25
### Fix
- Prioritize `config.json` over CLI arguments.

## [1.4.3] - 2024-12-20
### Fix
- Path handling in main function (fixed TypeError when processing command line arguments).

## [1.4.2] - 2024-12-20
### Feature
- Add `--noconfig` flag to override config file.

## [1.4.1] - 2024-12-20
### Fix
- Fixed event listener persistence for arrow key navigation between images.

## [1.4.0] - 2024-12-20
### Feature
- Add JSON configuration file support.

## [1.3.6] - 2024-12-20
### Feature
- Add keyboard navigation for preview images.

## [1.3.5] - 2024-12-20
### Refactor
- Decrease the default delay between models (from 6-12 to 3-6 seconds).

## [1.3.4] - 2024-12-20
### Fix
- Improve preview image metadata handling.

## [1.3.3] - 2024-11-29
### Refactor
- Increase model's thumbnail size in the model browser.

## [1.3.2] - 2024-11-29
### Fix
- Handle duplicate file message in clean operation.

## [1.3.1] - 2024-11-29
### Fix
- The scale effect in the model's gallery now affects videos.

## [1.3.0] - 2024-11-29
### Feature
- Enhance image modal with detailed metadata display (seed, prompt used, etc.).

## [1.2.5] - 2024-11-29
### Feature
- Enhance model browser search functionality.

## [1.2.4] - 2024-11-29
### Feature
- Enhance `--clean` to detect and handle duplicate models.

## [1.2.3] - 2024-11-29
### Feature
- Add toggleable cover images to model browser.

## [1.2.2] - 2024-11-29
### Feature
- Add `--skipmissing` option for optimizing model checks.

## [1.2.1] - 2024-11-29
### Fix
- Prevent missing models from appearing in multiple sections.

## [1.2.0] - 2024-11-29
### Feature
- Add video preview support for model galleries.
