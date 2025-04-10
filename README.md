# Interactive Data Manager

See full documentation [here](docs/README.md).

Check changes with pre-commit hooks: ```pre-commit run --all-files```

A Python-based desktop application to manage, view, and interact with user data using a customizable, themeable GUI. Supports dynamic user profiles, light/dark mode, and user-specific preferences.

## 🚀 Features

- Dynamic user profiles with separate settings.
- Dark and light mode themes with GUI palette switching.
- Profile-specific configuration and data management.
- Search functionality to filter data.
- GUI-based profile creation and selection.
- Data loading and saving with backup support.
- Interactive data table with editable cells and auto-saving.
- Hourly backups with change detection and retention cap.
- GUI label showing time since last successful save.

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/interactive-data.git
cd interactive-data
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## ⚙ Usage

- **Create Profile**: On first run, or by clicking 'Add Profile' button.
- **Switch Profiles**: Use the dropdown to switch between existing profiles.
- **Select Theme**: Choose between Light and Dark mode. The preference is saved per profile.
- **Search Data**: Use the search bar to filter through loaded data.

## 🧪 Testing

Run tests using pytest:
```bash
pytest tests/
```

## 💡 Planned Features

See [ROADMAP.md](./ROADMAP.md) for a list of planned and in-progress features.

## 🤝 Contributing

Contributions are welcome! Please open issues and submit pull requests for improvements and new features.

---

_Made with ❤️ for productivity and customization._
