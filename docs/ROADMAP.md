# Project Roadmap

## ✅ Completed Milestones

### Version 1.0.0
- Initial Python GUI with dark/light theme selector.
- DataManager for loading, saving, and backing up data.
- Basic search bar to filter user data.
- Configuration system for storing user preferences.

### Version 1.1.0
- Dynamic user profile creation and management.
- Profile-specific theme settings (light/dark mode).
- Theme applied automatically on app startup.
- 'Add Profile' button in GUI for real-time profile creation.

### Version 1.2.0
- Implemented editable QTableView for displaying and modifying user data.
- Connected table to live config files via DataManager.
- Automatic saving of changes every 5 minutes if data was modified.
- Hourly backups stored in /backups, with a cap of 10 most recent versions.
- Dirty-flag system tracks unsaved changes to prevent unnecessary disk writes.
- GUI label dynamically displays “Last saved: X minutes ago.”
- Full test coverage for save behavior, backup cap, dirty flag logic, and save timers.

---

## 🚧 In Progress

- Visual data display (table view).
- Sorting and filtering system (user-configurable).
- Named sort/filter configurations saved per profile.

---

## 🗺 Planned Features

### User Data Interaction
- Editable data entries with add/remove capability.
- Tagging system for flexible data categorization.
- User-defined functions for calculated fields (e.g., "Available" based on date).

### User Experience Improvements
- Undo/Redo system for user actions.
- GUI tooltips and help popups.
- Interactive data features like clickable links.

### Maintenance & Quality
- Auto-save and periodic backup system.
- Robust error handling and validation.

---

## 💡 Future Ideas

- Multi-language (localization) support.
- Cloud synchronization/multi-device support.
- Plugin system for custom user extensions.
- Data visualization (charts, graphs).
- Profile export/import feature.

---

_This roadmap evolves with the project. Stay tuned for updates!_
