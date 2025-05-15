import asyncio
import random
import re

from gpt4free.g4f import Provider
from gpt4free.g4f.client import AsyncClient


class G4fProvider:
    TIMEOUT_RESPONSE = 20  # Таймаут ожидания ответа в секундах
    CJK_PATTERN = re.compile(
        r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]"  # Диапазоны для CJK
    )

    def __init__(self):
        self.model_providers = {
            "gpt-4o-mini": [
                Provider.Blackbox,
                Provider.Chatai,
                Provider.DDG,
                Provider.Liaobots,
                # Provider.Pizzagpt,
                Provider.PollinationsAI,
            ],
            "gpt-4": [
                Provider.Blackbox,
                Provider.Copilot,
                Provider.DDG,
                Provider.PollinationsAI,
                Provider.Yqcloud,
            ],
            "gemini-1.5-flash": [
                Provider.Dynaspark,
                Provider.Free2GPT,
                Provider.FreeGpt,
                Provider.GizAI,
                Provider.TeachAnything,
                Provider.Websim,
            ],
            # "deepseek-r1": [
            #     Provider.Blackbox,
            #     Provider.DeepInfraChat,
            #     Provider.Glider,
            #     Provider.Jmuz,
            #     Provider.LambdaChat,
            #     Provider.Liaobots,
            #     Provider.PollinationsAI,
            #     Provider.TypeGPT,
            # ],
            "gpt-4o": [
                Provider.Blackbox,
                Provider.ChatGptEs,
                # Provider.DDG,
                Provider.Liaobots,
                # Provider.PollinationsAI,
            ],
        }
        self.client = AsyncClient(
            proxies="http://1GuhvSY3sNbA:RNW78Fm5@pool.proxy.market:10000", verify=False
        )

    async def gpt_request(self, prompt: str, models_list: list) -> str:
        # client = AsyncClient(
        #     # proxies="http://z0hul7ReoAXH:RNW78Fm5@pool.proxy.market:10000",
        #     # verify=False
        # )
        for model in models_list:
            providers = self.model_providers.get(model, [])
            if not providers:
                print(f"[!] Нет провайдеров для модели {model}")
                continue

            # Перемешиваем провайдеры для текущей модели
            # random.shuffle(providers)

            for provider in providers:
                try:
                    # инициализируем клиент с указанием провайдера и прокси
                    # client = AsyncClient(
                    #     provider=provider,
                    #     proxies='http://z0hul7ReoAXH:RNW78Fm5@pool.proxy.market:10000',
                    #     verify=False
                    # )

                    print(provider)
                    response = await asyncio.wait_for(
                        self.client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=random.uniform(
                                0.4, 0.8
                            ),  # Контроль креативности (0-1)
                            max_tokens=random.randint(300, 500),  # Лимит токенов
                            web_search=False,  # Отключение веб-поиска
                            stream=False,
                        ),
                        timeout=self.TIMEOUT_RESPONSE,
                    )

                    content = response.choices[0].message.content

                    # Проверка на CJK-символы
                    if self.CJK_PATTERN.search(content):
                        raise Exception(
                            f"Обнаружены CJK-символы в ответе провайдера {provider}"
                        )

                    if any(
                        msg in content.lower()
                        for msg in ["limit", "error", "blocked", "reached", "misuse"]
                    ):
                        raise Exception("Обнаружено достижение лимита")

                    # Удаляем блоки <think> с содержимым
                    clean_result = re.sub(
                        r"<think>.*?</think>",
                        "",
                        content,
                        flags=re.DOTALL,
                    ).strip()

                    return clean_result
                except asyncio.TimeoutError:
                    print(
                        f"[!] Таймаут в {self.TIMEOUT_RESPONSE}сек. истек для {provider} (модель {model}), иду дальше"
                    )
                    continue

                except Exception as e:
                    print(
                        f"[!] Ошибка {provider} (модель {model}), иду дальше: {str(e)}"
                    )
                    continue

        raise Exception("Все провайдеры исчерпаны")
