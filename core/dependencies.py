from config.config import API_TOKEN, CHAT_ID
from core.services.auth_service import AuthService
from core.services.client_service import TelegramClientService
from core.services.error_service import ErrorHandlerService
from core.services.notification_service import NotificationService
from core.use_cases.account_selection_uc import AccountSelectionUseCase
from core.use_cases.ai_commenting_uc import AICommentingUseCase
from core.use_cases.auth_uс import AuthUseCase
from core.use_cases.forwarding_uc import ForwardingUseCase
from core.use_cases.mass_forwarding_uc import MassForwardUseCase
from core.use_cases.mass_pars_channel_list_uc import MassParseChannelListUseCase
from core.use_cases.mass_pars_chat_list_uc import MassParseChatListUseCase
from core.use_cases.pars_chat_list_uc import ParsChatListUseCase
from core.utils.message_utils import MessageUtils
from core.utils.proxy_utils import ProxyUtils
from core.utils.randomized_utils import RandomizedUtils
from core.utils.tg_urls_utils import TelegramUrlsUtils
from infrastructure.converters.tdata_converter import TDataConverter
from infrastructure.external.g4f_provider import G4fProvider
from infrastructure.repositories.account_repo import AccountRepository
from infrastructure.repositories.blacklist_repo import BlacklistRepository
from infrastructure.repositories.csv_repo import CSVRepository
from infrastructure.repositories.excel_repo import ExcelRepository
from infrastructure.repositories.session_repo import SessionRepository
from infrastructure.repositories.txt_repo import TxtRepository


class Dependencies:
    def __init__(self):
        # Инициализируем все зависимости
        self.account_repo = AccountRepository()
        self.session_repo = SessionRepository()
        self.csv_repo = CSVRepository()
        self.proxy_utils = ProxyUtils()
        self.converter = TDataConverter()
        self.message_utils = MessageUtils()
        self.excel_repo = ExcelRepository()
        self.randomized_utils = RandomizedUtils()
        self.tg_urls_utils = TelegramUrlsUtils()
        self.blacklist_repo = BlacklistRepository()
        self.txt_repo = TxtRepository()

        # External
        self.ai_provider = G4fProvider()

        # Сервисы
        self.auth_service = AuthService(
            self.account_repo, self.session_repo, self.proxy_utils, self.converter
        )
        self.error_handler_service = ErrorHandlerService(self.account_repo)
        self.client_service = TelegramClientService(
            self.auth_service, self.account_repo
        )
        self.notification_service = NotificationService(API_TOKEN, CHAT_ID)

        # Use Cases
        self.auth_uc = AuthUseCase(self.auth_service, self.account_repo)
        self.forwarding_uc = ForwardingUseCase(
            self.client_service,
            self.account_repo,
            self.csv_repo,
            self.message_utils,
            self.randomized_utils,
            self.tg_urls_utils,
            self.error_handler_service,
        )
        self.mass_forwarding_uc = MassForwardUseCase(
            self.error_handler_service,
            self.client_service,
            self.forwarding_uc,
            self.account_repo,
            self.randomized_utils,
            self.tg_urls_utils,
            self.csv_repo,
        )
        self.pars_chat_list_uc = ParsChatListUseCase(
            self.client_service,
            self.account_repo,
            self.message_utils,
            self.csv_repo,
            self.excel_repo,
        )
        self.account_selection_uc = AccountSelectionUseCase(self.account_repo)
        self.mass_pars_chat_list_uc = MassParseChatListUseCase(
            self.client_service,
            self.account_repo,
            self.csv_repo,
            self.excel_repo,
            self.message_utils,
            self.randomized_utils,
            self.notification_service,
        )
        self.ai_commenting_uc = AICommentingUseCase(
            self.account_repo,
            self.client_service,
            self.blacklist_repo,
            self.mass_forwarding_uc,
            self.ai_provider,
            self.tg_urls_utils,
        )
        self.mass_pars_channel_list_uc = MassParseChannelListUseCase(
            self.client_service,
            self.account_repo,
            self.txt_repo,
            self.excel_repo,
            self.message_utils,
            self.randomized_utils,
            self.notification_service,
        )
