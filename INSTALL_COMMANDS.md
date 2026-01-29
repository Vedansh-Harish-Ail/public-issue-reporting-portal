# 📦 Installation Commands

To set up the environment for **Meri Panchayat**, run the following commands based on your operating system:

### 🪟 Windows (Powershell / CMD)
```powershell
pip install flask werkzeug gunicorn
```
*Alternatively, you can just run:*
```powershell
.\install_packages.bat
```

### 🍎 macOS / 🐧 Linux
```bash
pip3 install flask werkzeug gunicorn
```

---

### 📑 Automated Install from requirements.txt
If you have `requirements.txt` in your directory, simply run:
```bash
pip install -r requirements.txt
```

### ✅ Verification
To check if everything is installed correctly, run:
```bash
python -c "import flask; import werkzeug; print('Setup Successful!')"
```
