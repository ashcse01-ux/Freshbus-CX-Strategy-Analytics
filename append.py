rapwith open('script.js', 'r', encoding='utf-8') as f:
    content = f.read()
with open('C:/Users/Ayush Jain/.gemini/antigravity-ide/brain/a8419ef3-5dda-4634-9767-ae6095772f72/scratch/excel_js.txt', 'r', encoding='utf-8') as f2:
    new_logic = f2.read()

content = content.replace('})();', new_logic + '\n})();')

with open('script.js', 'w', encoding='utf-8') as f3:
    f3.write(content)
