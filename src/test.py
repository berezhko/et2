import unittest
import sys
import logging

logger = logging.getLogger(__name__)

from src.misc import md5
from src.misc import check_test


class TestOutput(unittest.TestCase):
    UNIXTIME = None
    OUTPUT_DIR = None
    TEST_CASE = None
    
    # Словари для хранения результатов
    _test_results = {}
    _correct_data = []

    @classmethod
    def setUpClass(cls):
        cls._test_results = {}
        cls._correct_data = []
        logger.info(f"Запуск тестирования...")

    @classmethod
    def tearDownClass(cls):
        # Вывод информации о неудачных тестах
        if cls._test_results:
            print("\nНеудачные тесты:", file=sys.stderr)
            for test_name, error_info in cls._test_results.items():
                print(f"\n{test_name}:\t{error_info}", end="", file=sys.stderr)
            bad_tests = [f"{t}:\t{e}" for t, e in cls._test_results.items()]
            logger.info(f"Неудачные тесты:\n{'\n'.join(bad_tests)}")

        # Вывод корректных данных для обновления конфига
        if cls._test_results and cls._correct_data:
            print("\n\nКорректные данные по Тестам:\ntests:", file=sys.stderr)
            for data in cls._correct_data:
                print(f"  - {data}", file=sys.stderr)
            print("\n", file=sys.stderr)
            logger.info(f"Корректные данные по Тестам:\n\ntests:\n  - {'\n  - '.join(cls._correct_data)}")
        logger.info(f"Тестирование окончено!")
        

    def compare(self, file_prefix, md5sum, ext):
        """Вспомогательная функция для сравнения файлов"""
        result = check_test(file_prefix, self.UNIXTIME, md5sum, self.OUTPUT_DIR)
        if result:
            return result[0]
        return "Не найдено подходящих файлов для сравнения!"

    @classmethod
    def create_test_method(cls, test_name, expected_md5, ext, file_prefix):
        """Динамически создает метод теста"""
        def test_method(self):
            file_path = f"{self.OUTPUT_DIR}/{file_prefix}-{self.UNIXTIME}.{ext}"
            actual_md5 = md5(file_path)
            # Сохраняем корректные данные
            correct_data = f"['{actual_md5}', '{ext}', '{file_prefix}']"
            self.__class__._correct_data.append(correct_data)
            try:
                self.assertEqual(actual_md5, expected_md5)
            except AssertionError as e:
                # Если тест не прошел, сохраняем информацию об ошибке
                self.__class__._test_results[test_name] = self.compare(file_prefix, expected_md5, ext)
                raise e

        # Устанавливаем docstring с префиксом из конфига
        test_method.__doc__ = f"{file_prefix}"
        return test_method

    @classmethod
    def generate_tests(cls):
        """Генерирует тесты на основе конфигурации"""
        if not cls.TEST_CASE:
            return
        count_tests = len(cls.TEST_CASE)
        num = lambda x: len(str(x))
        for i, test_data in enumerate(cls.TEST_CASE, 1):
            expected_md5, ext, file_prefix = test_data
            test_name = f"test_{"0".join(['' for i in range(1+num(count_tests)-num(i))])}{i}"
            test_method = cls.create_test_method(test_name, expected_md5, ext, file_prefix)
            setattr(cls, test_name, test_method)