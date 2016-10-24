import unittest
from django.contrib.auth.models import User
import mock
from sundog.constants import STATUS_CODENAME_PREFIX, CACHE_IMPORT_EXPIRATION
from sundog.services import (
    check_client_exists,
    check_client_exists_by_identification,
    check_client_type_exists,
    check_username_exists,
    get_participants_options,
    get_users_by_ids,
    get_user_status_permissions,
)


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.mock_user = mock.Mock(spec=User)
        self.mock_user.id = 123

    @mock.patch("sundog.services.Permission")
    def test_get_user_status_permissions_success(self, mock_permission):
        permission = mock.Mock()
        permission.name = "Can use status open"
        mock_permission.objects.filter.return_value = [permission]
        self.mock_user.get_all_permissions.return_value = ['sundog.view_all_files', 'sundog.can_use_status_open']
        result = get_user_status_permissions(self.mock_user)
        expected_result = ['OPEN']
        self.assertListEqual(result, expected_result)
        self.assertEqual(self.mock_user.get_all_permissions.call_count, 1)

    def test_get_user_status_permissions_none(self):
        result = get_user_status_permissions(None)
        self.assertIsNone(result)

    @mock.patch("sundog.services.Permission")
    @mock.patch("sundog.services.User")
    @mock.patch("sundog.services.logger")
    def test_get_participants_options_status_none_exception(self, mock_logger, mock_user_class, mock_permission_class):
        mock_file_id = 1
        expected_result = None
        mock_logger.error.return_value = None
        mock_user1 = mock.Mock(spec=User)
        mock_user2 = mock.Mock(spec=User)
        mock_user3 = mock.Mock(spec=User)
        mock_user1.id = 1
        mock_user2.id = 2
        mock_user3.id = 3
        participants_array = [mock_user1, mock_user2, mock_user3]
        mock_current_status = None

        result = get_participants_options(mock_file_id, mock_current_status, participants_array)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.Permission")
    @mock.patch("sundog.services.User")
    @mock.patch("sundog.services.logger")
    def test_get_participants_options_participants_none_success(self, mock_logger, mock_user_class, mock_permission_class):
        mock_file_id = 1
        expected_result = []
        mock_logger.error.return_value = None
        mock_permission = mock.Mock()
        mock_current_status = mock.Mock()
        mock_codename = STATUS_CODENAME_PREFIX + 'open'
        mock_current_status.get_permission_codename.return_value = mock_codename
        mock_permission_class.objects.get.return_value = mock_permission
        participants_array = None
        mock_current_status = mock_current_status
        mock_exclude = mock.Mock()
        mock_exclude.filter.return_value.distinct.return_value = expected_result
        mock_user_class.objects.exclude.return_value = mock_exclude

        result = get_participants_options(mock_file_id, mock_current_status, participants_array)

        mock_permission_class.objects.get.assert_called_once_with(codename=mock_codename)
        self.assertEqual(mock_user_class.objects.exclude.call_count, 1)
        self.assertEqual(mock_exclude.filter.call_count, 1)
        self.assertEqual(mock_logger.error.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.User")
    @mock.patch("sundog.services.logger")
    def test_get_users_by_ids_success(self, mock_logger, mock_user_class):
        mock_user_ids = [1, 2, 3]
        expected_result = []
        mock_logger.error.return_value = None
        mock_user_class.objects.filter.return_value = expected_result

        result = get_users_by_ids(mock_user_ids)

        mock_user_class.objects.filter.assert_called_once_with(id__in=mock_user_ids)
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_logger.error.call_count, 0)

    @mock.patch("sundog.services.User")
    @mock.patch("sundog.services.logger")
    def test_get_users_by_ids_exception(self, mock_logger, mock_user_class):
        mock_user_ids = [1, 2, 3]
        expected_result = None
        mock_logger.error.return_value = None
        mock_user_class.objects.filter.side_effect = Exception()

        result = get_users_by_ids(mock_user_ids)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_user_class.objects.filter.call_count, 1)

    @mock.patch("sundog.services.User")
    @mock.patch("sundog.services.logger")
    def test_get_users_by_ids_none_exception(self, mock_logger, mock_user_class):
        mock_user_ids = None
        expected_result = None
        mock_logger.error.return_value = None
        mock_user_class.objects.filter.side_effect = Exception()

        result = get_users_by_ids(mock_user_ids)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_user_class.objects.filter.call_count, 1)

    @mock.patch("sundog.services.ClientType")
    @mock.patch("sundog.services.cache")
    def test_check_client_type_exists_cache_success(self, mock_cache, mock_clienttype_class):
        mock_clienttype_name = "PERSON"
        mock_clienttype_name_key = "client_type_person"
        expected_result = 1
        mock_cache.get.return_value = expected_result
        mock_cache.set.return_value = True
        mock_clienttype_class.objects.get.return_value = None

        result = check_client_type_exists(mock_clienttype_name)

        self.assertEqual(mock_cache.set.call_count, 0)
        mock_cache.get.assert_called_once_with(mock_clienttype_name_key)
        self.assertEqual(mock_clienttype_class.objects.get.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.ClientType")
    @mock.patch("sundog.services.cache")
    def test_check_client_type_exists_no_cache_success(self, mock_cache, mock_clienttype_class):
        mock_clienttype_mame = "PERSON"
        mock_clienttype_name_key = "client_type_person"
        expected_result = 1
        mock_clienttype_result = mock.Mock()
        mock_clienttype_result.client_type_id = expected_result
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_clienttype_class.objects.get.return_value = mock_clienttype_result

        result = check_client_type_exists(mock_clienttype_mame)

        mock_cache.get.assert_called_once_with(mock_clienttype_name_key)
        mock_cache.set.assert_called_once_with(mock_clienttype_name_key, expected_result, CACHE_IMPORT_EXPIRATION)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.ClientType")
    @mock.patch("sundog.services.cache")
    @mock.patch("sundog.services.logger")
    def test_check_client_type_exists_no_cache_exception(self, mock_logger, mock_cache, mock_clienttype_class):
        mock_clienttype_mame = "PERSON"
        expected_result = None
        mock_logger.error.return_value = None
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_clienttype_class.objects.get.side_effect = Exception()

        result = check_client_type_exists(mock_clienttype_mame)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(mock_cache.set.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.Client")
    @mock.patch("sundog.services.cache")
    def test_check_client_exists_cache_success(self, mock_cache, mock_client_class):
        mock_client_name = "CLIENT"
        expected_result = 1
        mock_cache.get.return_value = expected_result
        mock_cache.set.return_value = True
        mock_client_class.objects.get.return_value = None

        result = check_client_exists(mock_client_name, None)

        self.assertEqual(mock_cache.set.call_count, 0)
        self.assertEqual(mock_cache.get.call_count, 1)
        self.assertEqual(mock_client_class.objects.get.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.Client")
    @mock.patch("sundog.services.cache")
    def test_check_client_exists_no_cache_success(self, mock_cache, mock_client_class):
        mock_client_mame = "CLIENT"
        mock_client_mame_key = "client_client"
        expected_result = 1
        mock_client_result = mock.Mock()
        mock_client_result.client_id = expected_result
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_client_class.objects.get.return_value = mock_client_result

        result = check_client_exists(mock_client_mame, None)

        mock_cache.get.assert_called_once_with(mock_client_mame_key)
        mock_cache.set.assert_called_once_with(mock_client_mame_key, expected_result, CACHE_IMPORT_EXPIRATION)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.Client")
    @mock.patch("sundog.services.cache")
    @mock.patch("sundog.services.logger")
    def test_check_client_exists_no_cache_exception(self, mock_logger, mock_cache, mock_client_class):
        mock_client_mame = "CLIENT"
        expected_result = None
        mock_logger.error.return_value = None
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_client_class.objects.get.side_effect = Exception()

        result = check_client_exists(mock_client_mame, None)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(mock_cache.set.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.Client")
    @mock.patch("sundog.services.cache")
    def test_check_client_exists_by_id_cache_success(self, mock_cache, mock_client_class):
        mock_client_id = "123 456"
        mock_client_id_key = 'client_ident_123_456'
        expected_result = 1
        mock_cache.get.return_value = expected_result
        mock_cache.set.return_value = True
        mock_client_class.objects.get.return_value = None

        result = check_client_exists_by_identification(mock_client_id, None)

        self.assertEqual(mock_cache.set.call_count, 0)
        mock_cache.get.assert_called_once_with(mock_client_id_key)
        self.assertEqual(mock_client_class.objects.get.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.Client")
    @mock.patch("sundog.services.cache")
    def test_check_client_exists_by_id_no_cache_success(self, mock_cache, mock_client_class):
        mock_client_id = "123 456"
        mock_client_id_key = 'client_ident_123_456'
        expected_result = 1
        mock_client_result = mock.Mock()
        mock_client_result.client_id = expected_result
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_client_class.objects.get.return_value = mock_client_result

        result = check_client_exists_by_identification(mock_client_id, None)

        mock_cache.get.assert_called_once_with(mock_client_id_key)
        mock_client_class.objects.get.assert_called_once_with(identification=mock_client_id)
        mock_cache.set.assert_called_once_with(mock_client_id_key, expected_result, CACHE_IMPORT_EXPIRATION)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.Client")
    @mock.patch("sundog.services.cache")
    @mock.patch("sundog.services.logger")
    def test_check_client_exists_by_id_no_cache_exception(self, mock_logger, mock_cache, mock_client_class):
        mock_client_id = "123 456"
        expected_result = None
        mock_logger.error.return_value = None
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_client_class.objects.get.side_effect = Exception()

        result = check_client_exists_by_identification(mock_client_id, None)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(mock_cache.set.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.User")
    @mock.patch("sundog.services.cache")
    def test_check_username_exists_cache_success(self, mock_cache, mock_user_class):
        mock_user_name = "user1"
        mock_user_name_key = "username_user1"
        expected_result = 1
        mock_cache.get.return_value = expected_result
        mock_cache.set.return_value = True
        mock_user_class.objects.get.return_value = None

        result = check_username_exists(mock_user_name)

        self.assertEqual(mock_cache.set.call_count, 0)
        mock_cache.get.assert_called_once_with(mock_user_name_key)
        self.assertEqual(mock_user_class.objects.get.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.User")
    @mock.patch("sundog.services.cache")
    def test_check_username_exists_no_cache_success(self, mock_cache, mock_user_class):
        mock_user_name = "user1"
        mock_user_name_key = 'username_user1'
        expected_result = mock.Mock(spec=User)
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_user_class.objects.get.return_value = expected_result

        result = check_username_exists(mock_user_name)

        mock_cache.get.assert_called_once_with(mock_user_name_key)
        mock_user_class.objects.get.assert_called_once_with(username=mock_user_name)
        mock_cache.set.assert_called_once_with(mock_user_name_key, expected_result, CACHE_IMPORT_EXPIRATION)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.User")
    @mock.patch("sundog.services.cache")
    @mock.patch("sundog.services.logger")
    def test_check_username_exists_no_cache_exception(self, mock_logger, mock_cache, mock_user_class):
        mock_username = "user1"
        expected_result = None
        mock_logger.error.return_value = None
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_user_class.objects.get.side_effect = Exception()

        result = check_username_exists(mock_username)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(mock_cache.set.call_count, 0)
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()
