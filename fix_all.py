# fix_all.py
import os

FIXES = {
    'Â·': '·',
    'Ã©': 'é',
    'Ã¨': 'è',
    'Ã ': 'à',
    'Ã¢': 'â',
    'Ã¹': 'ù',
    'Ã´': 'ô',
    'Ã®': 'î',
    'Ã«': 'ë',
    'Ã¯': 'ï',
    'Ã§': 'ç',
    'Å"': 'œ',
    'â€"': '—',
    'â€™': ''',
    'â€œ': '"',
    'â€': '"',
    'âš ï¸': '⚠️',
    'Â«': '«',
    'Â»': '»',
    'â€¯': '…',
    'Â°': '°',
    'Â ': ' ',
    'Ã‰': 'É',
    'Ã€': 'À',
    'Ã‡': 'Ç',
    'Ã”': 'Ô',
}

count_files = 0
count_fixes = 0

for root, _, files in os.walk('templates'):
    for f in files:
        if f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fh:
                content = fh.read()

            original = content
            for bad, good in FIXES.items():
                content = content.replace(bad, good)

            if content != original:
                with open(p, 'w', encoding='utf-8') as fh:
                    fh.write(content)
                count_files += 1
                count_fixes += 1
                print(f'✅ Corrigé : {p}')

print(f'\n🎉 {count_files} fichier(s) corrigé(s)')
