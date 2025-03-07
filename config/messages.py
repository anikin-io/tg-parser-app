# Сообщения для уведомлений и консольного вывода
MESSAGES = {
    "start_sending": "[+] Отправка сообщения для: {name} с аккаунта {phone}",
    "message_limit_reached": "[!] Лимит сообщений для аккаунта {phone} достигнут. Останавливаю рассылку.",
    "user_not_found": "[!] Пользователь {name} не найден ни по username, ни по user_id",
    "waiting": "[+] Ожидаю {sleep_time} секунд [{phone}]",
    "error": "[!] Ошибка при отправке сообщения пользователю {name} с аккаунта {phone}: {error}",
    "spam_warning": "[!] Получил предупреждение о спаме от Телеграма. Аккаунт {phone} заблокирован.",
    "searching_participants": "Ищу участников с логинами, начинающимися на '{char}'...",
    "not_authorized": "[!] Не удалось авторизовать аккаунт {phone}.",
    "request_code": "[+] Введите код для аккаунта {phone}: ",
    "request_password": "[+] Введите пароль для двухфакторной аутентификации: ",
    "message_sent": "[+] Сообщение успешно отправлено пользователю {name}.",
    "failed_to_get_participants": "[!] Не удалось получить участников чата по username группы: {error}",
    "failed_to_join_channel": "[!] Не удалось вступить в чат или получить участников через username группы: {error}",
    "not_found_username": "[!] Пользователь с username {username} не найден: {error}",
    "not_found_user_id": "[!] Пользователь с ID {user_id} не найден напрямую, пробуем через чат",
    "user_not_found_by_username_and_id": "[!] Не удалось найти пользователя {name} ни по username, ни по user_id",
    "input_number_of_accounts": "[+] Введите количество аккаунтов для рассылки (всего свободных {all_accounts}): ",
    "sending_completed": "[!] Готово. Сообщение разослано всем пользователям из базы",
    "choose_database": "[+] Доступные базы данных:",
    "input_choice": "[!] Введите номер базы для рассылки:",
    "reset_status": "[+] Сброс статуса 'в работе' для аккаунта: {phone}",
    "no_free_accounts": "[!] Недостаточно свободных аккаунтов. Доступно только {available}.",
    "no_available_accounts": "[!] Нет доступных свободных аккаунтов для рассылки.",
    "user_not_found": "[!] Аккаунт {name} не может использоваться, статус: {error}",
}
