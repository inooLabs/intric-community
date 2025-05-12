import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from intric.integration.domain.entities.user_integration import UserIntegration
from intric.integration.domain.factories.user_integration_factory import (
    UserIntegrationFactory,
)


class TestUserIntegrationFactory(unittest.TestCase):
    def setUp(self):
        # Create a mock tenant integration to use in tests
        self.tenant_integration_mock = MagicMock()
        self.tenant_integration_mock.id = uuid4()

    def test_create_entity(self):
        # Arrange
        user_id = uuid4()
        integration_id = uuid4()
        db_record = MagicMock()
        db_record.id = integration_id
        db_record.authenticated = True
        db_record.tenant_integration = self.tenant_integration_mock
        db_record.user_id = user_id

        # Act
        user_integration = UserIntegrationFactory.create_entity(db_record)

        # Assert
        self.assertIsInstance(user_integration, UserIntegration)
        self.assertEqual(user_integration.id, integration_id)
        self.assertEqual(user_integration.authenticated, True)
        self.assertEqual(
            user_integration.tenant_integration, self.tenant_integration_mock
        )
        self.assertEqual(user_integration.user_id, user_id)

    def test_create_entities(self):
        # Arrange
        num_records = 3
        db_records = []

        for i in range(num_records):
            record = MagicMock()
            record.id = uuid4()
            record.authenticated = bool(i % 2)  # Alternate between True and False
            record.tenant_integration = self.tenant_integration_mock
            record.user_id = uuid4()
            db_records.append(record)

        # Act
        user_integrations = UserIntegrationFactory.create_entities(db_records)

        # Assert
        self.assertEqual(len(user_integrations), num_records)

        for i, user_integration in enumerate(user_integrations):
            self.assertIsInstance(user_integration, UserIntegration)
            self.assertEqual(user_integration.id, db_records[i].id)
            self.assertEqual(
                user_integration.authenticated, db_records[i].authenticated
            )
            self.assertEqual(
                user_integration.tenant_integration, self.tenant_integration_mock
            )
            self.assertEqual(user_integration.user_id, db_records[i].user_id)


if __name__ == "__main__":
    unittest.main()
