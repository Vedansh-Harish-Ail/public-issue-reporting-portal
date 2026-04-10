import os
import glob

# Step 1: Inject get_image_url into app.py
app_file = "app.py"
with open(app_file, "r", encoding="utf-8") as f:
    app_content = f.read()

context_processor = """
@app.context_processor
def utility_processor():
    def get_image_url(path):
        if not path:
            return ""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        from flask import url_for
        return url_for('static', filename=path)
    return dict(get_image_url=get_image_url)

"""

if "def get_image_url" not in app_content:
    # Insert it right before the routes, let's say after configuration
    app_content = app_content.replace("# ---------------- CITIZEN ROUTES --------------", context_processor + "# ---------------- CITIZEN ROUTES --------------")
    with open(app_file, "w", encoding="utf-8") as f:
        f.write(app_content)


# Step 2: Update templates
templates_dir = "templates"
for root, dirs, files in os.walk(templates_dir):
    for filename in files:
        if filename.endswith(".html"):
            filepath = os.path.join(root, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Cases to replace:
            # url_for('static', filename=i.photo_path) -> get_image_url(i.photo_path)
            # url_for('static', filename=n.banner_path) -> get_image_url(n.banner_path)
            # url_for('static', filename=a.image_path) -> get_image_url(a.image_path)
            # url_for('static', filename=issue.photo_path) -> get_image_url(issue.photo_path)
            
            import re
            # Regex to match url_for('static', filename=VARIABLE)
            # We want to replace it with get_image_url(VARIABLE) ONLY if VARIABLE is one of the model paths
            def replacer(match):
                var = match.group(1)
                # don't replace static assets like 'css/style.css'
                if var.startswith("'") or var.startswith('"'):
                    return match.group(0)
                return f"get_image_url({var})"
            
            new_content = re.sub(r"url_for\('static',\s*filename=([^)]+)\)", replacer, content)
            
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {filepath}")
