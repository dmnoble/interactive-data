# Developer Notes

A living document to capture insights, lessons learned, and development reflections while building the Interactive Data Manager.

---

## 🛠 General Development Notes

- **Project Structure**: Organized into `src/` for code, `tests/` for unit tests, and `config_profiles/` for user-specific configurations.
- **User Profiles**: Profiles dynamically created and stored in `config_profiles/`, each with separate settings and preferences.
- **Theme System**: QPalette is used for runtime theme switching between light and dark modes.
- **DataManager**: Handles JSON-based data storage, with plans to expand into more complex data handling and backup management.

---

## 💡 Lessons Learned

### Milestone: Dynamic Profile Creation
- **Challenge**: Handling profile creation when none exist on startup.
- **Solution**: Use `QInputDialog` for user input and dynamically update the profile selector.
- **Future Consideration**: Optionally validate profile names (e.g., no spaces, unique names).

### Milestone: Theme Switching
- **Challenge**: Applying dark/light mode dynamically without GUI refresh issues.
- **Solution**: Use `QPalette` and adjust all necessary color roles; apply on theme selector change.
- **Improvement Idea**: Add more customization (font size, button colors).

### Milestone: Undo/Redo with Recovery
- **Goal**: Implement an undo/redo system that survives crashes and supports GUI history tracking.

#### 🧪 Testing & Troubleshooting
- **Problem**: Tests crashed or hung silently when triggering PyQt5 GUI elements (e.g., recovery prompt).
- **Solution**:
  - Introduced `IDW_TEST_MODE` environment variable to suppress GUI prompts during test runs
  - Patched CI with `QT_QPA_PLATFORM=offscreen` to prevent PyQt from rendering GUI on headless Linux runners

#### 🛠 Integration Notes
- **Log Versioning**: Added a `"version": 1` field to `.undo_log.json` for future-proofing

---

## 🚀 Future Dev Ideas & Reminders

- **Add error handling** when loading/saving corrupted config/data files.
- **Profile management improvements**: allow rename/delete profiles directly from the GUI.
- **Consider using PyQt's model-view architecture** for scalable data display and editing.
- **Explore modular GUI design** for better separation of concerns (data view vs. config panel).
- **Profile switching autosave**: Ensure autosave triggers before switching profiles to preserve changes and clear temporary undo log.

---

## 🔧 To Investigate

- How to handle large datasets efficiently in QTableWidget or other PyQt components.
- Best way to implement undo/redo with complex data interactions.
- Security considerations for storing sensitive user data in future versions.

---

_Updated regularly as development continues._
