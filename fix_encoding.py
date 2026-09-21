import os

def fix_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    try:
        fixed = content.encode('cp1252').decode('utf-8')
        return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        return content


# Parcourir tous les templates HTML
count = 0
for root, dirs, files in os.walk('templates'):
    for filename in files:
        if filename.endswith('.html'):
            path = os.path.join(root, filename)
            fixed = fix_file(path)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(fixed)
            count += 1
            print(f"✅ {path}")

print(f"\n🎉 {count} fichiers réparés")