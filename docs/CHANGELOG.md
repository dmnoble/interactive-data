# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2024-04-03
### Added
- Editable QTableView connected to real user data
- Auto-saving every 5 minutes using a dirty flag system
- Hourly backups saved to a dedicated /backups directory
- Backup files limited to the 10 most recent to prevent bloat
- Timestamped backup file naming for traceable history
- GUI indicator showing "Last saved: X minutes ago" with live updates

### Fixed
- Data saving now only triggers on real changes to reduce redundant writes
- Edge case errors (e.g. write failures) are now logged and handled

### Test Coverage
- Added unit tests for dirty flag behavior, save error handling, backup cap enforcement, and label update logic

This marks the completion of the data table feature branch and paves the way for advanced editing features like undo/redo and filtering.

## [1.1.0] - 2024-03-05
### Added
- Dynamic user profile creation with default settings.
- 'Add Profile' button in MainWindow to allow new profiles anytime.
- Profile-specific theme (light/dark) selection saved per user.
- Theme switching dynamically updates GUI colors using QPalette.

### Changed
- Theme now applies automatically on startup based on selected profile.

## [1.0.0] - 2024-02-21
### Added
- Initial Python GUI with dark/light mode theme selector.
- Basic search bar to search user data.
- DataManager for loading and saving data.
- Basic config system to store user preferences in `config.json`.

---

_This changelog will be updated with each milestone or significant feature/fix._
