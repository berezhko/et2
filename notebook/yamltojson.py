#!/usr/bin/env python
# coding: utf-8

import sys
import json
import yaml

def yaml_to_json(input_stream, output_stream):
    """
    Конвертирует YAML данные из входного потока в JSON и записывает в выходной поток
    """
    try:
        data = yaml.safe_load(input_stream)
        json.dump(data, output_stream, indent=2, ensure_ascii=False)
        output_stream.write('\n')  # Добавляем перенос строки в конце
        return True
    except Exception as e:
        sys.stderr.write(f"Ошибка конвертации: {str(e)}\n")
        return False

def main():
    # Определение источников данных
    input_file = sys.stdin
    output_file = sys.stdout
    
    # Обработка аргументов командной строки
    input_path = None
    output_path = None
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    # Открытие файлов при необходимости
    try:
        if input_path:
            input_file = open(input_path, 'r', encoding='cp1251')
        
        if output_path:
            output_file = open(output_path, 'w', encoding='utf-8')
        
        # Выполнение конвертации
        success = yaml_to_json(input_file, output_file)
        
        # Возвращаем соответствующий код выхода
        sys.exit(0 if success else 1)
        
    finally:
        # Закрываем файлы, если мы их открывали
        if input_path and input_file != sys.stdin:
            input_file.close()
        if output_path and output_file != sys.stdout:
            output_file.close()

if __name__ == "__main__":
    main()
