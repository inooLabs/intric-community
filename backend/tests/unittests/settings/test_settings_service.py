from intric.settings.setting_service import SettingService
from intric.settings.settings import SettingsInDB, SettingsPublic, SettingsUpsert
from tests.fixtures import TEST_USER, TEST_UUID

TEST_SETTINGS = SettingsPublic()
TEST_SETTINGS_EXPECTED = SettingsInDB(
    user_id=TEST_USER.id,
    id=TEST_UUID,
)


class MockRepo:
    def __init__(self):
        self.settings = {}

    async def get(self, user_id):
        return self.settings.get(user_id)

    async def add(self, settings: SettingsUpsert):
        settings_in_db = SettingsInDB(**settings.model_dump(), id=TEST_UUID)
        self.settings[settings.user_id] = settings_in_db
        return settings_in_db

    async def update(self, settings: SettingsUpsert):
        curr_settings = self.settings[settings.user_id]
        settings_in_db = SettingsInDB(**settings.model_dump(), id=curr_settings.id)
        self.settings[settings.user_id] = settings_in_db
        return settings_in_db


async def test_get_settings_if_settings():
    repo = MockRepo()

    repo.settings[TEST_USER.id] = TEST_SETTINGS_EXPECTED

    service = SettingService(repo=repo, user=TEST_USER, ai_models_service=MockRepo())

    settings = await service.get_settings()

    assert settings == TEST_SETTINGS_EXPECTED


async def test_update_settings():
    repo = MockRepo()
    service = SettingService(repo=repo, user=TEST_USER, ai_models_service=MockRepo())

    repo.settings[TEST_USER.id] = TEST_SETTINGS_EXPECTED
    new_settings = SettingsPublic(chatbot_widget={"colour": "blue"})
    settings_expected = SettingsInDB(
        **new_settings.model_dump(), id=TEST_UUID, user_id=TEST_USER.id
    )

    settings = await service.update_settings(new_settings)

    assert settings == settings_expected
    assert repo.settings[TEST_USER.id] == settings_expected
