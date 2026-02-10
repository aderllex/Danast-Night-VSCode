#!/usr/bin/env python3
"""
Скрипт для регулировки насыщенности цветов в теме VS Code.
Использование: python adjust_saturation.py <значение от 0.1 до 1.0>
Где 1.0 = оригинальная насыщенность, 0.5 = половина насыщенности, и т.д.
"""

import json
import re
import sys
from pathlib import Path


def hex_to_rgb(hex_color):
    """Конвертирует hex цвет в RGB."""
    hex_color = hex_color.lstrip('#')
    # Обработка цветов с альфа-каналом (8 символов)
    if len(hex_color) == 8:
        r, g, b, a = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), hex_color[6:8]
        return r, g, b, a
    elif len(hex_color) == 6:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return r, g, b, None
    return None


def rgb_to_hsl(r, g, b):
    """Конвертирует RGB в HSL."""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2.0

    if max_c == min_c:
        h = s = 0.0
    else:
        d = max_c - min_c
        s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
        
        if max_c == r:
            h = (g - b) / d + (6.0 if g < b else 0.0)
        elif max_c == g:
            h = (b - r) / d + 2.0
        else:
            h = (r - g) / d + 4.0
        h /= 6.0

    return h, s, l


def hsl_to_rgb(h, s, l):
    """Конвертирует HSL в RGB."""
    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p

    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)

    return int(r * 255), int(g * 255), int(b * 255)


def rgb_to_hex(r, g, b, alpha=None):
    """Конвертирует RGB в hex."""
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    if alpha:
        hex_color += alpha
    return hex_color


def is_colorful(hex_color, saturation_threshold=0.15):
    """Проверяет, является ли цвет цветным (не серым)."""
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return False
    
    r, g, b = rgb[0], rgb[1], rgb[2]
    h, s, l = rgb_to_hsl(r, g, b)
    
    # Цвет считается цветным, если его насыщенность выше порога
    return s > saturation_threshold


def adjust_color_saturation(hex_color, saturation_factor):
    """Изменяет насыщенность цвета."""
    if not is_colorful(hex_color):
        return hex_color
    
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return hex_color
    
    r, g, b = rgb[0], rgb[1], rgb[2]
    alpha = rgb[3] if len(rgb) == 4 else None
    
    h, s, l = rgb_to_hsl(r, g, b)
    
    # Изменяем насыщенность
    s = s * saturation_factor
    s = max(0, min(1, s))  # Ограничиваем значение [0, 1]
    
    r, g, b = hsl_to_rgb(h, s, l)
    return rgb_to_hex(r, g, b, alpha)


def process_value(value, saturation_factor):
    """Обрабатывает значение (может быть строкой с цветом или словарем)."""
    if isinstance(value, str) and value.startswith('#'):
        return adjust_color_saturation(value, saturation_factor)
    elif isinstance(value, dict):
        return process_dict(value, saturation_factor)
    elif isinstance(value, list):
        return [process_value(item, saturation_factor) for item in value]
    return value


def process_dict(data, saturation_factor):
    """Рекурсивно обрабатывает словарь и изменяет все цвета."""
    result = {}
    for key, value in data.items():
        if isinstance(value, str) and value.startswith('#'):
            result[key] = adjust_color_saturation(value, saturation_factor)
        elif isinstance(value, dict):
            result[key] = process_dict(value, saturation_factor)
        elif isinstance(value, list):
            result[key] = [process_value(item, saturation_factor) for item in value]
        else:
            result[key] = value
    return result


def main():
    if len(sys.argv) != 2:
        print("Использование: python adjust_saturation.py <значение от 0.1 до 1.0>")
        print("Пример: python adjust_saturation.py 0.7")
        sys.exit(1)
    
    try:
        saturation_factor = float(sys.argv[1])
        if saturation_factor < 0.1 or saturation_factor > 1.0:
            raise ValueError()
    except ValueError:
        print("Ошибка: значение должно быть числом от 0.1 до 1.0")
        sys.exit(1)
    
    # Находим файл темы
    script_dir = Path(__file__).parent
    theme_file = script_dir / 'themes' / 'Danast-Night.json'
    backup_file = script_dir / 'themes' / 'Danast-Night.backup.json'
    
    if not theme_file.exists():
        print(f"Ошибка: файл темы не найден: {theme_file}")
        sys.exit(1)
    
    # Создаем резервную копию при первом запуске
    if not backup_file.exists():
        print(f"Создаю резервную копию: {backup_file}")
        with open(theme_file, 'r', encoding='utf-8') as f:
            backup_data = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(backup_data)
    
    # Читаем тему
    with open(theme_file, 'r', encoding='utf-8') as f:
        theme_data = json.load(f)
    
    print(f"Применяю коэффициент насыщенности: {saturation_factor}")
    
    # Обрабатываем все цвета
    modified_theme = process_dict(theme_data, saturation_factor)
    
    # Сохраняем измененную тему
    with open(theme_file, 'w', encoding='utf-8') as f:
        json.dump(modified_theme, f, indent='\t', ensure_ascii=False)
    
    print(f"✓ Тема успешно обновлена!")
    print(f"  Перезагрузите окно VS Code (Ctrl+R), чтобы увидеть изменения.")
    print(f"  Для восстановления оригинала используйте: {backup_file}")


if __name__ == '__main__':
    main()
