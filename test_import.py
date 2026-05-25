import sys
sys.path.insert(0, r'C:\Girls-AI\Girls')

from replacements import apply_replacements, fix_before_spell

# Тестируем
test_text = "тплый свет настольной лампы"
print(f"Было: {test_text}")
print(f"Стало: {apply_replacements(test_text)}")