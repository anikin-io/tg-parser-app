import random


class RandomizedUtils:
    @staticmethod
    def get_randomized_delay(base_delay: int, variation: int = 5) -> float:
        """
        Генерирует случайную задержку в диапазоне base_delay ± variation
        с защитой от отрицательных значений
        """
        randomized = base_delay + random.uniform(-variation, variation)
        return float(max(30.0, randomized))  # Минимум 30 секунд чтобы избежать нуля
