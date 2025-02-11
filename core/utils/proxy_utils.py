import aiohttp


class ProxyUtils:
    @staticmethod
    async def check_ip(proxy=None):
        proxies = None
        if proxy:
            proxy_url = f"socks5://{proxy['username']}:{proxy['password']}@{proxy['addr']}:{proxy['port']}"
            proxies = proxy_url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://ip-api.com/json/", proxy=proxies
                ) as response:
                    if response.status != 200:
                        print("[!] Прокси нерабочие. Завершение работы скрипта.")
                        return False

                    data = await response.json()
                    city = data.get("city", "Неизвестно")
                    print(
                        f"[+] Проверка IP: {data['query']} (Страна: {data['country']}, Город: {city})"
                    )
                    return True

        except Exception as e:
            print(f"[!] Не удалось проверить IP: {str(e)}")
            return False