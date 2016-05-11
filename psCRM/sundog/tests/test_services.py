import unittest
from django.contrib.auth.models import User
from sundog.models import Tag, MyFile
import mock
from sundog.constants import STATUS_CODENAME_PREFIX, CACHE_IMPORT_EXPIRATION, IMPORT_CLIENT_EXCEL_HEADERS, IMPORT_FILE_EXCEL_HEADERS
from sundog.services import get_user_status_permissions, get_files_by_user, get_status_list_by_user, \
    get_file_by_id_for_user, create_access_file_history, get_default_status, get_access_file_history, \
    get_file_documents, get_participants_options, get_users_by_ids, get_completed_by_file_status, check_client_type_exists, \
    check_client_exists, check_client_exists_by_identification, check_status_exists, check_username_exists, check_tag_exists, \
    upload_import_file, upload_import_client


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.mock_user = mock.Mock(spec=User)
        self.mock_user.id = 123

    def test_get_user_status_permissions_success(self):
        self.mock_user.get_all_permissions.return_value = ['sundog.view_all_files', 'sundog.can_use_status_open']
        result = get_user_status_permissions(self.mock_user)
        expected_result = ['OPEN']
        self.assertListEqual(result, expected_result)
        self.assertEqual(self.mock_user.get_all_permissions.call_count, 1)

    def test_get_user_status_permissions_none(self):
        result = get_user_status_permissions(None)
        self.assertIsNone(result)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_files_by_user_superuser_admin_success(self, mock_status_permissions, mock_myfile_class):
        mock_status_permissions.return_value = ['OPEN']

        all_files = []
        mock_myfile_class.objects.all.return_value = all_files
        self.mock_user.is_superuser = True
        result = get_files_by_user(self.mock_user, True)

        self.assertListEqual(result, all_files)
        self.assertEqual(mock_status_permissions.call_count, 0)
        self.assertEqual(mock_myfile_class.objects.filter.call_count, 0)
        self.assertEqual(mock_myfile_class.objects.all.call_count, 1)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_files_by_user_superuser_no_admin_success(self, mock_status_permissions, mock_myfile_class):
        mock_status_permissions.return_value = ['OPEN']

        all_files = []
        mock_myfile_class.objects.all.return_value = None
        mock_myfile_class.objects.filter.return_value = all_files
        self.mock_user.is_superuser = True
        result = get_files_by_user(self.mock_user, False)

        self.assertEqual(mock_status_permissions.call_count, 0)
        self.assertEqual(mock_myfile_class.objects.all.call_count, 0)
        mock_myfile_class.objects.filter.assert_called_once_with(active=True)
        self.assertListEqual(result, all_files)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_files_by_user_no_superuser_admin_success(self, mock_status_permissions, mock_myfile_class):
        permissions_array = ['OPEN']
        mock_status_permissions.return_value = permissions_array
        all_files = []
        mock_myfile_class.objects.all.return_value = None
        mock_myfile_class.objects.filter.return_value = all_files
        self.mock_user.is_superuser = False
        self.mock_user.has_perm.return_value = True
        result = get_files_by_user(self.mock_user, True)

        self.assertListEqual(result, all_files)
        self.assertEqual(mock_status_permissions.call_count, 1)
        self.assertEqual(mock_myfile_class.objects.all.call_count, 0)
        mock_myfile_class.objects.filter.assert_called_once_with(current_status__name__in=permissions_array)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_files_by_user_no_superuser_no_admin_success(self, mock_status_permissions, mock_myfile_class):
        permissions_array = ['OPEN']
        mock_status_permissions.return_value = permissions_array
        all_files = []
        mock_myfile_class.objects.all.return_value = None
        mock_myfile_class.objects.filter.return_value = all_files
        self.mock_user.is_superuser = False
        self.mock_user.has_perm.return_value = True
        result = get_files_by_user(self.mock_user, False)

        self.assertListEqual(result, all_files)
        self.assertEqual(mock_status_permissions.call_count, 1)
        self.assertEqual(mock_myfile_class.objects.all.call_count, 0)
        mock_myfile_class.objects.filter.assert_called_once_with(active=True, current_status__name__in=permissions_array)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_files_by_user_no_all_files_admin_success(self, mock_status_permissions, mock_myfile_class):
        permissions_array = ['OPEN']
        mock_status_permissions.return_value = permissions_array
        all_files = []
        mock_myfile_class.objects.all.return_value = None
        mock_myfile_class.objects.filter.return_value = all_files
        self.mock_user.is_superuser = False
        self.mock_user.has_perm.return_value = False
        result = get_files_by_user(self.mock_user, True)

        self.assertListEqual(result, all_files)
        self.assertEqual(mock_status_permissions.call_count, 1)
        self.assertEqual(mock_myfile_class.objects.all.call_count, 0)
        mock_myfile_class.objects.filter.assert_called_once_with(current_status__name__in=permissions_array,
                                                                 participants__id=self.mock_user.id)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_files_by_user_no_all_files_no_admin_success(self, mock_status_permissions, mock_myfile_class):
        permissions_array = ['OPEN']
        mock_status_permissions.return_value = permissions_array
        all_files = []
        mock_myfile_class.objects.all.return_value = None
        mock_myfile_class.objects.filter.return_value = all_files
        self.mock_user.is_superuser = False
        self.mock_user.has_perm.return_value = False
        result = get_files_by_user(self.mock_user, False)

        self.assertListEqual(result, all_files)
        self.assertEqual(mock_status_permissions.call_count, 1)
        self.assertEqual(mock_myfile_class.objects.all.call_count, 0)
        mock_myfile_class.objects.filter.assert_called_once_with(active=True, current_status__name__in=permissions_array,
                                                                 participants__id=self.mock_user.id)

    @mock.patch("sundog.services.FileStatus")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_status_list_by_user_superuser_admin_success(self, mock_status_permissions, mock_filestatus_class):
        permissions_array = ['OPEN']
        all_status = []
        mock_status_permissions.return_value = permissions_array
        mock_filestatus_class.objects.all.return_value.order_by.return_value = all_status
        self.mock_user.is_superuser = True

        result = get_status_list_by_user(self.mock_user, True)

        self.assertEqual(mock_status_permissions.call_count, 0)
        self.assertEqual(mock_filestatus_class.objects.filter.call_count, 0)
        self.assertEqual(mock_filestatus_class.objects.all.call_count, 1)
        self.assertListEqual(result, all_status)

    @mock.patch("sundog.services.FileStatus")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_status_list_by_user_superuser_no_admin_success(self, mock_status_permissions, mock_filestatus_class):
        permissions_array = ['OPEN']
        all_status = []
        mock_status_permissions.return_value = permissions_array
        mock_filestatus_class.objects.all.return_value.order_by.return_value = None
        mock_filestatus_class.objects.filter.return_value.order_by.return_value = all_status
        self.mock_user.is_superuser = True

        result = get_status_list_by_user(self.mock_user)

        self.assertEqual(mock_status_permissions.call_count, 0)
        self.assertEqual(mock_filestatus_class.objects.all.call_count, 0)
        self.assertEqual(mock_filestatus_class.objects.filter.call_count, 1)
        mock_filestatus_class.objects.filter.assert_called_once_with(active=True)
        self.assertListEqual(result, all_status)

    @mock.patch("sundog.services.FileStatus")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_status_list_by_user_no_superuser_admin_success(self, mock_status_permissions, mock_filestatus_class):
        permissions_array = ['OPEN']
        all_status = []
        mock_status_permissions.return_value = permissions_array
        mock_filestatus_class.objects.all.return_value.order_by.return_value = None
        mock_filestatus_class.objects.filter.return_value.order_by.return_value = all_status
        self.mock_user.is_superuser = False

        result = get_status_list_by_user(self.mock_user, True)

        self.assertEqual(mock_status_permissions.call_count, 1)
        self.assertEqual(mock_filestatus_class.objects.all.call_count, 0)
        self.assertEqual(mock_filestatus_class.objects.filter.call_count, 1)
        mock_filestatus_class.objects.filter.assert_called_once_with(name__in=permissions_array)
        self.assertListEqual(result, all_status)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.save_access_file_history")
    def test_get_file_by_id_for_user_superuser_success(self, mock_save_access_function, mock_myfile_class):
        mock_my_file_result = mock.Mock()
        mock_file_id = 1
        mock_myfile_class.objects.get.return_value = mock_my_file_result
        self.mock_user.is_superuser = True
        result = get_file_by_id_for_user(mock_file_id, self.mock_user)

        self.assertEqual(result, mock_my_file_result)
        mock_save_access_function.assert_called_once_with(mock_file_id, self.mock_user)
        self.assertEqual(self.mock_user.has_perm.call_count, 0)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.save_access_file_history")
    def test_get_file_by_id_for_user_no_superuser_no_permission_success(self, mock_save_access_function, mock_myfile_class):
        mock_file_id = 1
        mock_my_file_result = mock.Mock()
        mock_my_file_result.current_status.get_permission_codename.return_value = STATUS_CODENAME_PREFIX + 'Open'

        mock_myfile_class.objects.get.return_value = mock_my_file_result
        self.mock_user.is_superuser = False
        self.mock_user.get_all_permissions.return_value = []
        result = get_file_by_id_for_user(mock_file_id, self.mock_user)

        self.assertEqual(result, "Unavailable")
        self.assertEqual(mock_save_access_function.call_count, 0)
        self.assertEqual(self.mock_user.has_perm.call_count, 0)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.save_access_file_history")
    def test_get_file_by_id_for_user_no_superuser_all_files_success(self, mock_save_access_function, mock_myfile_class):
        mock_file_id = 1
        mock_my_file_result = mock.Mock()
        mock_my_file_result.current_status.get_permission_codename.return_value = STATUS_CODENAME_PREFIX + 'open'

        mock_myfile_class.objects.get.return_value = mock_my_file_result
        self.mock_user.is_superuser = False
        self.mock_user.has_perm.return_value = True
        self.mock_user.get_all_permissions.return_value = ['sundog.view_all_files', 'sundog.can_use_status_open']
        result = get_file_by_id_for_user(mock_file_id, self.mock_user)

        self.mock_user.has_perm.assert_called_once_with('sundog.view_all_files')
        self.assertEqual(result, mock_my_file_result)
        self.assertEqual(mock_save_access_function.call_count, 1)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.save_access_file_history")
    def test_get_file_by_id_for_user_no_superuser_participant_success(self, mock_save_access_function, mock_myfile_class):
        mock_file_id = 1
        mock_my_file_result = mock.Mock()
        mock_my_file_result.current_status.get_permission_codename.return_value = STATUS_CODENAME_PREFIX + 'open'
        mock_my_file_result.participants.all.return_value = [self.mock_user]
        mock_myfile_class.objects.get.return_value = mock_my_file_result
        self.mock_user.is_superuser = False
        self.mock_user.has_perm.return_value = False
        self.mock_user.get_all_permissions.return_value = ['sundog.can_use_status_open']
        result = get_file_by_id_for_user(mock_file_id, self.mock_user)

        self.mock_user.has_perm.assert_called_once_with('sundog.view_all_files')
        self.assertEqual(result, mock_my_file_result)
        self.assertEqual(mock_save_access_function.call_count, 1)
        self.assertEqual(mock_my_file_result.participants.all.call_count, 1)

    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.save_access_file_history")
    def test_get_file_by_id_for_user_no_superuser_no_participant_success(self, mock_save_access_function, mock_myfile_class):
        mock_file_id = 1
        mock_my_file_result = mock.Mock()
        mock_my_file_result.current_status.get_permission_codename.return_value = STATUS_CODENAME_PREFIX + 'open'
        mock_my_file_result.participants.all.return_value = []
        mock_myfile_class.objects.get.return_value = mock_my_file_result
        self.mock_user.is_superuser = False
        self.mock_user.has_perm.return_value = False
        self.mock_user.get_all_permissions.return_value = ['sundog.can_use_status_open']
        result = get_file_by_id_for_user(mock_file_id, self.mock_user)

        self.mock_user.has_perm.assert_called_once_with('sundog.view_all_files')
        self.assertEqual(result, "Unavailable")
        self.assertEqual(mock_save_access_function.call_count, 0)
        self.assertEqual(mock_my_file_result.participants.all.call_count, 1)

    @mock.patch("sundog.services.FileStatus")
    @mock.patch("sundog.services.cache")
    def test_get_default_status_cache(self, mock_cache, mock_filestatus_class):
        mock_status_id = 1
        mock_cache.get.return_value = mock_status_id
        mock_cache.set.return_value = True
        mock_filestatus_class.objects.filter.return_value = None

        result = get_default_status()

        self.assertEqual(mock_cache.set.call_count, 0)
        self.assertEqual(mock_cache.get.call_count, 1)
        self.assertEqual(mock_filestatus_class.objects.filter.call_count, 0)
        self.assertEqual(result, mock_status_id)

    @mock.patch("sundog.services.FileStatus")
    @mock.patch("sundog.services.cache")
    def test_get_default_status_no_cache(self, mock_cache, mock_filestatus_class):
        mock_status_id = 1
        mock_status_result = mock.Mock()
        mock_status_result.status_id = mock_status_id
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_filestatus_class.objects.filter.return_value.order_by.return_value.__getitem__.return_value.get.return_value = mock_status_result

        result = get_default_status()

        self.assertEqual(mock_cache.get.call_count, 1)
        mock_cache.set.assert_called_once_with('default_status_id', mock_status_id, CACHE_IMPORT_EXPIRATION)
        self.assertEqual(result, mock_status_id)

    @mock.patch("sundog.services.FileAccessHistory")
    @mock.patch("sundog.services.datetime")
    def test_create_access_file_history_success(self, mock_datetime, mock_fileaccess_class):
        mock_file_id = 1
        mock_datetime.now.return_value = 201601200258
        mock_fileaccess_class.objects.create.return_value = True

        result = create_access_file_history(mock_file_id, self.mock_user)

        mock_fileaccess_class.objects.create.assert_called_once_with(file_id=mock_file_id, user_id=self.mock_user.id, time=mock_datetime.now.return_value)
        self.assertEqual(result, None)

    @mock.patch("sundog.services.FileAccessHistory")
    @mock.patch("sundog.services.logger")
    def test_create_access_file_history_exception(self, mock_logger, mock_fileaccess_class):
        mock_file_id = 1
        mock_logger.error.return_value = None
        mock_fileaccess_class.objects.create.return_value = True

        result = create_access_file_history(mock_file_id, None)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(result, None)
        self.assertEqual(mock_fileaccess_class.objects.create.call_count, 0)

    @mock.patch("sundog.services.FileAccessHistory")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_access_file_history_superuser_success(self, mock_status_permissions, mock_fileaccess_class):
        expected_result = []
        mock_fileaccess_class.objects.filter.return_value.order_by.return_value = []
        self.mock_user.is_superuser = True
        result = get_access_file_history(self.mock_user)

        mock_fileaccess_class.objects.filter.assert_called_once_with(user_id=self.mock_user.id)
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_status_permissions.call_count, 0)

    @mock.patch("sundog.services.FileAccessHistory")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_access_file_history_no_superuser_success(self, mock_status_permissions, mock_fileaccess_class):
        expected_result = []
        permissions_array = ['OPEN']
        mock_status_permissions.return_value = permissions_array
        mock_fileaccess_class.objects.filter.return_value.order_by.return_value = []
        self.mock_user.is_superuser = False
        self.mock_user.has_perm.return_value = True

        result = get_access_file_history(self.mock_user)

        mock_status_permissions.assert_called_once_with(self.mock_user)
        self.mock_user.has_perm.assert_called_once_with('sundog.view_all_files')
        mock_fileaccess_class.objects.filter.assert_called_once_with(user_id=self.mock_user.id,
                                                                     file__current_status__name__in=permissions_array)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.FileAccessHistory")
    @mock.patch("sundog.services.get_user_status_permissions")
    def test_get_access_file_history_no_superuser_no_all_files_success(self, mock_status_permissions, mock_fileaccess_class):
        expected_result = []
        permissions_array = ['OPEN']
        mock_status_permissions.return_value = permissions_array
        mock_fileaccess_class.objects.filter.return_value.order_by.return_value = []
        self.mock_user.is_superuser = False
        self.mock_user.has_perm.return_value = False

        result = get_access_file_history(self.mock_user)

        mock_status_permissions.assert_called_once_with(self.mock_user)
        self.mock_user.has_perm.assert_called_once_with('sundog.view_all_files')
        mock_fileaccess_class.objects.filter.assert_called_once_with(user_id=self.mock_user.id, file__participants__id=self.mock_user.id,
                                                                     file__current_status__name__in=permissions_array)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.FileAccessHistory")
    @mock.patch("sundog.services.logger")
    def test_get_access_file_history_exception(self, mock_logger, mock_fileaccess_class):
        expected_result = None
        mock_logger.error.return_value = None

        result = get_access_file_history(None)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.Document")
    @mock.patch("sundog.services.logger")
    def test_get_file_documents_success(self, mock_logger, mock_document_class):
        mock_file_id = 1
        expected_result = mock.Mock()
        mock_logger.error.return_value = None
        mock_document_class.objects.filter.return_value = expected_result

        result = get_file_documents(mock_file_id)

        mock_document_class.objects.filter.assert_called_once_with(file__file_id=mock_file_id)
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_logger.error.call_count, 0)

    @mock.patch("sundog.services.Document")
    @mock.patch("sundog.services.logger")
    def test_get_file_documents_exception(self, mock_logger, mock_document_class):
        mock_file_id = 1
        mock_logger.error.return_value = None
        mock_document_class.objects.filter.side_effect = Exception()

        result = get_file_documents(mock_file_id)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(result, None)
        self.assertEqual(mock_document_class.objects.filter.call_count, 1)

    @mock.patch("sundog.services.Document")
    @mock.patch("sundog.services.logger")
    def test_get_file_documents_none_exception(self, mock_logger, mock_document_class):
        mock_file_id = None
        mock_logger.error.return_value = None
        mock_document_class.objects.filter.side_effect = Exception()

        result = get_file_documents(mock_file_id)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(result, None)
        self.assertEqual(mock_document_class.objects.filter.call_count, 1)

    @mock.patch("sundog.services.Document")
    @mock.patch("sundog.services.logger")
    def test_get_file_documents_none_exception(self, mock_logger, mock_document_class):
        mock_file_id = None
        mock_logger.error.return_value = None
        mock_document_class.objects.filter.side_effect = Exception()

        result = get_file_documents(mock_file_id)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(result, None)
        self.assertEqual(mock_document_class.objects.filter.call_count, 1)

    @mock.patch("sundog.services.Permission")
    @mock.patch("sundog.services.User")
    def test_get_participants_options_success(self, mock_user_class, mock_permission_class):
        mock_file_id = 1
        expected_result = []
        mock_user1 = mock.Mock(spec=User)
        mock_user2 = mock.Mock(spec=User)
        mock_user3 = mock.Mock(spec=User)
        mock_user1.id = 1
        mock_user2.id = 2
        mock_user3.id = 3
        participants_array = [mock_user1, mock_user2, mock_user3]
        ids_array = [1, 2, 3]
        mock_permission = mock.Mock()
        mock_current_status = mock.Mock()
        mock_codename = STATUS_CODENAME_PREFIX + 'open'
        mock_current_status.get_permission_codename.return_value = mock_codename
        mock_permission_class.objects.get.return_value = mock_permission
        mock_exclude = mock.Mock()
        mock_exclude.filter.return_value.distinct.return_value = expected_result
        mock_user_class.objects.exclude.return_value = mock_exclude

        result = get_participants_options(mock_file_id, mock_current_status, participants_array)

        mock_permission_class.objects.get.assert_called_once_with(codename=mock_codename)
        mock_user_class.objects.exclude.assert_called_once_with(id__in=ids_array)
        self.assertEqual(mock_exclude.filter.call_count, 1)
        self.assertEqual(result, expected_result)

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

    @mock.patch("sundog.services.FileStatus")
    @mock.patch("sundog.services.logger")
    def test_get_completed_by_file_status_success(self, mock_logger, mock_status_class):
        mock_status_id = 1
        expected_result = 10
        mock_status = mock.Mock()
        mock_status.related_percent = expected_result
        mock_logger.error.return_value = None
        mock_status_class.objects.get.return_value = mock_status

        result = get_completed_by_file_status(mock_status_id)

        mock_status_class.objects.get.assert_called_once_with(status_id=mock_status_id)
        self.assertEqual(result, expected_result)
        self.assertEqual(mock_logger.error.call_count, 0)

    @mock.patch("sundog.services.FileStatus")
    @mock.patch("sundog.services.logger")
    def test_get_completed_by_file_status_exception(self, mock_logger, mock_status_class):
        mock_status_id = 1
        expected_result = 0
        mock_logger.error.return_value = None
        mock_status_class.objects.get.side_effect = Exception()

        result = get_completed_by_file_status(mock_status_id)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(result, expected_result)

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

        result = check_client_exists(mock_client_name)

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

        result = check_client_exists(mock_client_mame)

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

        result = check_client_exists(mock_client_mame)

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

        result = check_client_exists_by_identification(mock_client_id)

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

        result = check_client_exists_by_identification(mock_client_id)

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

        result = check_client_exists_by_identification(mock_client_id)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(mock_cache.set.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.FileStatus")
    @mock.patch("sundog.services.cache")
    def test_check_status_exists_cache_success(self, mock_cache, mock_status_class):
        mock_status_name = "SOME STATUS"
        mock_status_name_key = "status_some_status"
        expected_result = 1
        mock_cache.get.return_value = expected_result
        mock_cache.set.return_value = True
        mock_status_class.objects.get.return_value = None

        result = check_status_exists(mock_status_name)

        self.assertEqual(mock_cache.set.call_count, 0)
        mock_cache.get.assert_called_once_with(mock_status_name_key)
        self.assertEqual(mock_status_class.objects.get.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.FileStatus")
    @mock.patch("sundog.services.cache")
    def test_check_status_no_cache_success(self, mock_cache, mock_status_class):
        mock_status_name = "NEW STATUS"
        mock_status_key = 'status_new_status'
        expected_result = 1
        mock_client_result = mock.Mock()
        mock_client_result.status_id = expected_result
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_status_class.objects.get.return_value = mock_client_result

        result = check_status_exists(mock_status_name)

        mock_cache.get.assert_called_once_with(mock_status_key)
        mock_status_class.objects.get.assert_called_once_with(name=mock_status_name)
        mock_cache.set.assert_called_once_with(mock_status_key, expected_result, CACHE_IMPORT_EXPIRATION)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.FileStatus")
    @mock.patch("sundog.services.cache")
    @mock.patch("sundog.services.logger")
    def test_check_status_no_cache_exception(self, mock_logger, mock_cache, mock_status_class):
        mock_status = "NEW STATUS"
        expected_result = None
        mock_logger.error.return_value = None
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_status_class.objects.get.side_effect = Exception()

        result = check_status_exists(mock_status)

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

    @mock.patch("sundog.services.Tag")
    @mock.patch("sundog.services.cache")
    def test_check_tag_exists_cache_success(self, mock_cache, mock_tag_class):
        mock_tag_name = "tag test"
        mock_tag_name_key = "tag_tag_test"
        expected_result = 1
        mock_cache.get.return_value = expected_result
        mock_cache.set.return_value = True
        mock_tag_class.objects.get.return_value = None

        result = check_tag_exists(mock_tag_name)

        self.assertEqual(mock_cache.set.call_count, 0)
        mock_cache.get.assert_called_once_with(mock_tag_name_key)
        self.assertEqual(mock_tag_class.objects.get.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.Tag")
    @mock.patch("sundog.services.cache")
    def test_check_tag_exists_no_cache_success(self, mock_cache, mock_tag_class):
        mock_tag_name = "TAG TEST"
        mock_tag_name_key = "tag_tag_test"
        expected_result = mock.Mock(spec=Tag)
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_tag_class.objects.get.return_value = expected_result

        result = check_tag_exists(mock_tag_name)

        mock_cache.get.assert_called_once_with(mock_tag_name_key)
        mock_tag_class.objects.get.assert_called_once_with(name=mock_tag_name)
        mock_cache.set.assert_called_once_with(mock_tag_name_key, expected_result, CACHE_IMPORT_EXPIRATION)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.Tag")
    @mock.patch("sundog.services.cache")
    @mock.patch("sundog.services.logger")
    def test_check_tag_exists_no_cache_exception(self, mock_logger, mock_cache, mock_tag_class):
        mock_tag = "TAG TEST"
        expected_result = None
        mock_logger.error.return_value = None
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_tag_class.objects.get.side_effect = Exception()

        result = check_tag_exists(mock_tag)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.assertEqual(mock_cache.set.call_count, 0)
        self.assertEqual(result, expected_result)

    @mock.patch("sundog.services.open_workbook")
    @mock.patch("sundog.services.check_status_exists")
    @mock.patch("sundog.services.get_default_status")
    @mock.patch("sundog.services.check_client_exists")
    @mock.patch("sundog.services.save_import_history")
    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.xldate_as_tuple")
    @mock.patch("sundog.services.check_username_exists")
    @mock.patch("sundog.services.check_tag_exists")
    @mock.patch("sundog.services.FileStatusHistory")
    def test_upload_import_file_success(self, mock_file_status_history, mock_check_tag_exists, mock_check_username_exists, mock_xldate_as_tuple, mock_my_file_class, mock_save_import_history, mock_client_exists, mock_default_status, mock_status_exists, mock_open_workbook):
        mock_my_file = mock.Mock(spec=MyFile)
        mock_my_file.save.return_value = None
        mock_my_file.tags.add.return_value = None
        mock_my_file.participants.add.return_value = None
        mock_my_file.get_temp_tags.return_value = [1]
        mock_my_file.get_temp_users.return_value = [1]
        mock_my_file_class.return_value = mock_my_file
        mock_check_tag_exists.return_value = mock.Mock(spec=Tag)
        mock_check_username_exists.return_value = mock.Mock(spec=User)
        mock_file_status_history.return_value = mock.Mock()
        mock_file_status_history.return_value.create_new_file_status_history.return_value = None
        mock_xldate_as_tuple.return_value = (2015, 01, 25, 0, 0, 0)
        mock_save_import_history.return_value = True
        mock_client_exists.return_value = 1
        mock_default_status.return_value = 1
        mock_status_exists.return_value = 2
        mock_import_file = mock.Mock()
        mock_import_file.read.return_value = []
        mock_book = mock.Mock()
        mock_sheet = mock.Mock()
        mock_header_cell1 = mock.Mock()
        mock_header_cell1.value = 'description'
        mock_header_cell2 = mock.Mock()
        mock_header_cell2.value = 'status'
        mock_header_cell3 = mock.Mock()
        mock_header_cell3.value = 'client '
        mock_header_cell4 = mock.Mock()
        mock_header_cell4.value = 'priority'
        mock_header_cell5 = mock.Mock()
        mock_header_cell5.value = ' quoted price'
        mock_header_cell6 = mock.Mock()
        mock_header_cell6.value = ' quoted date'
        mock_header_cell7 = mock.Mock()
        mock_header_cell7.value = ' invoice price'
        mock_header_cell8 = mock.Mock()
        mock_header_cell8.value = ' invoice date'
        mock_header_cell9 = mock.Mock()
        mock_header_cell9.value = 'participant1'
        mock_header_cell10 = mock.Mock()
        mock_header_cell10.value = 'participant2'
        mock_header_cell11 = mock.Mock()
        mock_header_cell11.value = 'tag1'
        mock_header_cell12 = mock.Mock()
        mock_header_cell12.value = 'tag2'
        mock_header_cell13 = mock.Mock()
        mock_header_cell13.value = 'tag3'
        mock_header_cell14 = mock.Mock()
        mock_header_cell14.value = 'tag4'
        mock_header_cell15 = mock.Mock()
        mock_header_cell15.value = 'tag5'
        mock_description_cell = mock.Mock()
        mock_description_cell.value = 'some description'
        mock_status_cell = mock.Mock()
        mock_status_cell.value = 'some status'
        mock_client_cell = mock.Mock()
        mock_client_cell.value = 'some client'
        mock_priority_cell = mock.Mock()
        mock_priority_cell.value = 'high priority'
        mock_quotedprice_cell = mock.Mock()
        mock_quotedprice_cell.value = 1000
        mock_quoteddate_cell = mock.Mock()
        mock_quoteddate_cell.value = '02/12/2015'
        mock_invoiceprice_cell = mock.Mock()
        mock_invoiceprice_cell.value = 3000.587
        mock_invoicedate_cell = mock.Mock()
        mock_invoicedate_cell.value = '12/02/2016'
        mock_user_cell = mock.Mock()
        mock_user_cell.value = 'user1'
        mock_none_cell = mock.Mock()
        mock_none_cell.value = None
        mock_tag_cell = mock.Mock()
        mock_tag_cell.value = 'new tag'
        mock_sheet.cell.side_effect = [mock_header_cell1, mock_header_cell2, mock_header_cell3, mock_header_cell4, mock_header_cell5, \
                                       mock_header_cell6, mock_header_cell7, mock_header_cell8, mock_header_cell9, mock_header_cell10, \
                                       mock_header_cell11, mock_header_cell12, mock_header_cell13, mock_header_cell14, mock_header_cell15, \
                                       mock_description_cell, mock_status_cell, mock_client_cell, mock_priority_cell, \
                                       mock_quotedprice_cell, mock_quoteddate_cell, mock_invoiceprice_cell, mock_invoicedate_cell, \
                                       mock_user_cell, mock_none_cell, mock_none_cell, mock_none_cell, mock_tag_cell, mock_tag_cell, \
                                       mock_none_cell]
        mock_sheet.ncols = len(IMPORT_FILE_EXCEL_HEADERS)
        mock_sheet.nrows = 2
        mock_book.sheet_by_index.return_value = mock_sheet
        mock_open_workbook.return_value = mock_book
        expected_result = []

        result = upload_import_file(mock_import_file, self.mock_user)

        self.assertEqual(expected_result, result)
        self.assertEqual(mock_my_file_class.return_value.save.call_count, 2)
        self.assertEqual(mock_my_file.participants.add.call_count, 1)
        self.assertEqual(mock_my_file.tags.add.call_count, 1)
        self.assertEqual(mock_save_import_history.call_count, 1)
        self.assertEqual(mock_file_status_history.return_value.create_new_file_status_history.call_count, 1)

    @mock.patch("sundog.services.open_workbook")
    @mock.patch("sundog.services.check_status_exists")
    @mock.patch("sundog.services.get_default_status")
    @mock.patch("sundog.services.check_client_exists")
    @mock.patch("sundog.services.save_import_history")
    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.xldate_as_tuple")
    @mock.patch("sundog.services.check_username_exists")
    @mock.patch("sundog.services.check_tag_exists")
    @mock.patch("sundog.services.FileStatusHistory")
    def test_upload_import_file_row_errors_success(self, mock_file_status_history, mock_check_tag_exists, mock_check_username_exists, mock_xldate_as_tuple, mock_my_file_class, mock_save_import_history, mock_client_exists, mock_default_status, mock_status_exists, mock_open_workbook):
        mock_my_file = mock.Mock(spec=MyFile)
        mock_my_file.save.return_value = None
        mock_my_file.tags.add.return_value = None
        mock_my_file.participants.add.return_value = None
        mock_my_file.get_temp_tags.return_value = [1]
        mock_my_file.get_temp_users.return_value = [1]
        mock_my_file_class.return_value = mock_my_file
        mock_check_tag_exists.return_value = None
        mock_check_username_exists.return_value = None
        mock_file_status_history.return_value = mock.Mock()
        mock_file_status_history.return_value.create_new_file_status_history.return_value = None
        mock_xldate_as_tuple.side_effect = Exception()
        mock_save_import_history.return_value = True
        mock_client_exists.return_value = None
        mock_default_status.return_value = None
        mock_status_exists.return_value = None
        mock_import_file = mock.Mock()
        mock_import_file.read.return_value = []
        mock_book = mock.Mock()
        mock_sheet = mock.Mock()
        mock_header_cell1 = mock.Mock()
        mock_header_cell1.value = 'description'
        mock_header_cell2 = mock.Mock()
        mock_header_cell2.value = 'status'
        mock_header_cell3 = mock.Mock()
        mock_header_cell3.value = 'client '
        mock_header_cell4 = mock.Mock()
        mock_header_cell4.value = 'priority'
        mock_header_cell5 = mock.Mock()
        mock_header_cell5.value = ' quoted price'
        mock_header_cell6 = mock.Mock()
        mock_header_cell6.value = ' quoted date'
        mock_header_cell7 = mock.Mock()
        mock_header_cell7.value = ' invoice price'
        mock_header_cell8 = mock.Mock()
        mock_header_cell8.value = ' invoice date'
        mock_header_cell9 = mock.Mock()
        mock_header_cell9.value = 'participant1'
        mock_header_cell10 = mock.Mock()
        mock_header_cell10.value = 'participant2'
        mock_header_cell11 = mock.Mock()
        mock_header_cell11.value = 'tag1'
        mock_header_cell12 = mock.Mock()
        mock_header_cell12.value = 'tag2'
        mock_header_cell13 = mock.Mock()
        mock_header_cell13.value = 'tag3'
        mock_header_cell14 = mock.Mock()
        mock_header_cell14.value = 'tag4'
        mock_header_cell15 = mock.Mock()
        mock_header_cell15.value = 'tag5'
        mock_description_cell = mock.Mock()
        mock_description_cell.value = 'some description'
        mock_status_cell = mock.Mock()
        mock_status_cell.value = 'some status'
        mock_client_cell = mock.Mock()
        mock_client_cell.value = 'some client'
        mock_priority_cell = mock.Mock()
        mock_priority_cell.value = 'high priority'
        mock_quotedprice_cell = mock.Mock()
        mock_quotedprice_cell.value = 1000
        mock_quoteddate_cell = mock.Mock()
        mock_quoteddate_cell.value = '02/12/2015'
        mock_invoiceprice_cell = mock.Mock()
        mock_invoiceprice_cell.value = 3000.587
        mock_invoicedate_cell = mock.Mock()
        mock_invoicedate_cell.value = '12/02/2016'
        mock_user_cell = mock.Mock()
        mock_user_cell.value = 'user1'
        mock_none_cell = mock.Mock()
        mock_none_cell.value = None
        mock_tag_cell = mock.Mock()
        mock_tag_cell.value = 'new tag'
        mock_sheet.cell.side_effect = [mock_header_cell1, mock_header_cell2, mock_header_cell3, mock_header_cell4, mock_header_cell5, \
                                       mock_header_cell6, mock_header_cell7, mock_header_cell8, mock_header_cell9, mock_header_cell10, \
                                       mock_header_cell11, mock_header_cell12, mock_header_cell13, mock_header_cell14, mock_header_cell15, \
                                       mock_description_cell, mock_status_cell, mock_client_cell, mock_priority_cell, \
                                       mock_quotedprice_cell, mock_quoteddate_cell, mock_invoiceprice_cell, mock_invoicedate_cell, \
                                       mock_user_cell, mock_none_cell, mock_none_cell, mock_none_cell, mock_tag_cell, mock_tag_cell, \
                                       mock_none_cell]
        mock_sheet.ncols = len(IMPORT_FILE_EXCEL_HEADERS)
        mock_sheet.nrows = 2
        mock_book.sheet_by_index.return_value = mock_sheet
        mock_open_workbook.return_value = mock_book

        result = upload_import_file(mock_import_file, self.mock_user)

        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 7)
        self.assertEqual(mock_my_file_class.return_value.save.call_count, 0)
        self.assertEqual(mock_my_file.participants.add.call_count, 0)
        self.assertEqual(mock_my_file.tags.add.call_count, 0)
        self.assertEqual(mock_file_status_history.return_value.create_new_file_status_history.call_count, 0)
        self.assertEqual(mock_save_import_history.call_count, 0)

    @mock.patch("sundog.services.open_workbook")
    @mock.patch("sundog.services.check_status_exists")
    @mock.patch("sundog.services.get_default_status")
    @mock.patch("sundog.services.check_client_exists")
    @mock.patch("sundog.services.save_import_history")
    @mock.patch("sundog.services.MyFile")
    @mock.patch("sundog.services.xldate_as_tuple")
    @mock.patch("sundog.services.check_username_exists")
    @mock.patch("sundog.services.check_tag_exists")
    @mock.patch("sundog.services.FileStatusHistory")
    def test_upload_import_file_header_no_row_errors_success(self, mock_file_status_history, mock_check_tag_exists,
                                                             mock_check_username_exists, mock_xldate_as_tuple, mock_my_file_class, mock_save_import_history, mock_client_exists, mock_default_status, mock_status_exists, mock_open_workbook):
        mock_my_file = mock.Mock(spec=MyFile)
        mock_my_file.save.return_value = None
        mock_my_file.tags.add.return_value = None
        mock_my_file.participants.add.return_value = None
        mock_my_file.get_temp_tags.return_value = [1]
        mock_my_file.get_temp_users.return_value = [1]
        mock_my_file_class.return_value = mock_my_file
        mock_check_tag_exists.return_value = None
        mock_check_username_exists.return_value = None
        mock_file_status_history.return_value = mock.Mock()
        mock_file_status_history.return_value.create_new_file_status_history.return_value = None
        mock_xldate_as_tuple.side_effect = Exception()
        mock_save_import_history.return_value = True
        mock_client_exists.return_value = None
        mock_default_status.return_value = 1
        mock_status_exists.return_value = None
        mock_import_file = mock.Mock()
        mock_import_file.read.return_value = []
        mock_book = mock.Mock()
        mock_sheet = mock.Mock()
        mock_header_cell1 = mock.Mock()
        mock_header_cell1.value = 'description'
        mock_header_cell2 = mock.Mock()
        mock_header_cell2.value = 'status'
        mock_header_cell3 = mock.Mock()
        mock_header_cell3.value = 'client '
        mock_header_cell4 = mock.Mock()
        mock_header_cell4.value = 'priority'
        mock_header_cell5 = mock.Mock()
        mock_header_cell5.value = ' quoted price'
        mock_header_cell6 = mock.Mock()
        mock_header_cell6.value = ' quoted date'
        mock_header_cell7 = mock.Mock()
        mock_header_cell7.value = ' invoice price'
        mock_header_cell8 = mock.Mock()
        mock_header_cell8.value = ' invoice date'
        mock_header_cell9 = mock.Mock()
        mock_header_cell9.value = 'participant1'
        mock_header_cell11 = mock.Mock()
        mock_header_cell11.value = 'tag1'
        mock_header_cell12 = mock.Mock()
        mock_header_cell12.value = 'tag2'
        mock_header_cell13 = mock.Mock()
        mock_header_cell13.value = 'tag3'
        mock_header_cell14 = mock.Mock()
        mock_header_cell14.value = 'tag4'
        mock_header_cell15 = mock.Mock()
        mock_header_cell15.value = 'tag5'

        mock_sheet.cell.side_effect = [mock_header_cell1, mock_header_cell2, mock_header_cell3, mock_header_cell4, mock_header_cell5,
                                       mock_header_cell6, mock_header_cell7, mock_header_cell8, mock_header_cell9, mock_header_cell11,
                                       mock_header_cell12, mock_header_cell13, mock_header_cell14, mock_header_cell15]
        mock_sheet.ncols = len(IMPORT_FILE_EXCEL_HEADERS) - 1
        mock_sheet.nrows = 1
        mock_book.sheet_by_index.return_value = mock_sheet
        mock_open_workbook.return_value = mock_book

        result = upload_import_file(mock_import_file, self.mock_user)

        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 8)
        self.assertEqual(mock_my_file_class.return_value.save.call_count, 0)
        self.assertEqual(mock_my_file.participants.add.call_count, 0)
        self.assertEqual(mock_my_file.tags.add.call_count, 0)
        self.assertEqual(mock_file_status_history.return_value.create_new_file_status_history.call_count, 0)
        self.assertEqual(mock_save_import_history.call_count, 0)

    @mock.patch("sundog.services.open_workbook")
    @mock.patch("sundog.services.check_client_type_exists")
    @mock.patch("sundog.services.check_client_exists")
    @mock.patch("sundog.services.check_client_exists_by_identification")
    @mock.patch("sundog.services.check_username_exists")
    @mock.patch("sundog.services.save_import_history")
    @mock.patch("sundog.services.Client")
    def test_upload_import_client_success(self, mock_client_class, mock_save_import_history, mock_username_exists, mock_client_exists_by_id, mock_client_exists, mock_client_type_exists, mock_open_workbook):
        mock_client_class.objects.bulk_create.return_value = None
        mock_save_import_history.return_value = None
        mock_username_exists.return_value = mock.Mock(spec=User)
        mock_client_exists_by_id.return_value = None
        mock_client_exists.return_value = None
        mock_client_type_exists.return_value = 1
        mock_import_file = mock.Mock()
        mock_import_file.read.return_value = []
        mock_book = mock.Mock()
        mock_sheet = mock.Mock()
        mock_header_cell1 = mock.Mock()
        mock_header_cell1.value = 'client type'
        mock_header_cell2 = mock.Mock()
        mock_header_cell2.value = 'client name'
        mock_header_cell3 = mock.Mock()
        mock_header_cell3.value = 'identification '
        mock_header_cell4 = mock.Mock()
        mock_header_cell4.value = 'email'
        mock_header_cell5 = mock.Mock()
        mock_header_cell5.value = ' phone number'
        mock_header_cell6 = mock.Mock()
        mock_header_cell6.value = ' mobile number'
        mock_header_cell7 = mock.Mock()
        mock_header_cell7.value = ' country'
        mock_header_cell8 = mock.Mock()
        mock_header_cell8.value = ' state'
        mock_header_cell9 = mock.Mock()
        mock_header_cell9.value = ' city'
        mock_header_cell10 = mock.Mock()
        mock_header_cell10.value = 'zip code'
        mock_header_cell11 = mock.Mock()
        mock_header_cell11.value = 'address'
        mock_header_cell12 = mock.Mock()
        mock_header_cell12.value = 'related user'
        mock_client_type_cell = mock.Mock()
        mock_client_type_cell.value = 'some type here'
        mock_client_name_cell = mock.Mock()
        mock_client_name_cell.value = 'client name whatever'
        mock_client_id_cell = mock.Mock()
        mock_client_id_cell.value = '123 4568'
        mock_client_email_cell = mock.Mock()
        mock_client_email_cell.value = 'email@valid.id'
        mock_client_phone_cell = mock.Mock()
        mock_client_phone_cell.value = '132456888'
        mock_client_mobile_cell = mock.Mock()
        mock_client_mobile_cell.value = ''
        mock_client_country_cell = mock.Mock()
        mock_client_country_cell.value = ''
        mock_client_state_cell = mock.Mock()
        mock_client_state_cell.value = 'Florida'
        mock_client_city_cell = mock.Mock()
        mock_client_city_cell.value = 'some city'
        mock_client_zip_cell = mock.Mock()
        mock_client_zip_cell.value = '4545454'
        mock_client_address_cell = mock.Mock()
        mock_client_address_cell.value = '4545454'
        mock_client_user_cell = mock.Mock()
        mock_client_user_cell.value = 'user1'

        mock_sheet.cell.side_effect = [mock_header_cell1, mock_header_cell2, mock_header_cell3, mock_header_cell4, mock_header_cell5,
                                       mock_header_cell6, mock_header_cell7, mock_header_cell8, mock_header_cell9, mock_header_cell10,
                                       mock_header_cell11, mock_header_cell12, mock_client_type_cell, mock_client_name_cell,
                                       mock_client_id_cell, mock_client_email_cell, mock_client_phone_cell, mock_client_mobile_cell,
                                       mock_client_country_cell, mock_client_state_cell, mock_client_city_cell, mock_client_zip_cell,
                                       mock_client_address_cell, mock_client_user_cell]
        mock_sheet.ncols = len(IMPORT_CLIENT_EXCEL_HEADERS)
        mock_sheet.nrows = 2
        mock_book.sheet_by_index.return_value = mock_sheet
        mock_open_workbook.return_value = mock_book

        result = upload_import_client(mock_import_file, self.mock_user)

        self.assertEqual(result, [])
        self.assertEqual(mock_client_class.objects.bulk_create.call_count, 1)
        self.assertEqual(mock_save_import_history.call_count, 1)

    @mock.patch("sundog.services.open_workbook")
    @mock.patch("sundog.services.check_client_type_exists")
    @mock.patch("sundog.services.check_client_exists")
    @mock.patch("sundog.services.check_client_exists_by_identification")
    @mock.patch("sundog.services.check_username_exists")
    @mock.patch("sundog.services.save_import_history")
    @mock.patch("sundog.services.Client")
    def test_upload_import_client_row_errors(self, mock_client_class, mock_save_import_history, mock_username_exists, mock_client_exists_by_id, mock_client_exists, mock_client_type_exists, mock_open_workbook):
        mock_client_class.objects.bulk_create.return_value = None
        mock_save_import_history.return_value = None
        mock_username_exists.return_value = None
        mock_client_exists_by_id.return_value = 1
        mock_client_exists.return_value = 1
        mock_client_type_exists.return_value = None
        mock_import_file = mock.Mock()
        mock_import_file.read.return_value = []
        mock_book = mock.Mock()
        mock_sheet = mock.Mock()
        mock_header_cell1 = mock.Mock()
        mock_header_cell1.value = 'client type'
        mock_header_cell2 = mock.Mock()
        mock_header_cell2.value = 'client name'
        mock_header_cell3 = mock.Mock()
        mock_header_cell3.value = 'identification '
        mock_header_cell4 = mock.Mock()
        mock_header_cell4.value = 'email'
        mock_header_cell5 = mock.Mock()
        mock_header_cell5.value = ' phone number'
        mock_header_cell6 = mock.Mock()
        mock_header_cell6.value = ' mobile number'
        mock_header_cell7 = mock.Mock()
        mock_header_cell7.value = ' country'
        mock_header_cell8 = mock.Mock()
        mock_header_cell8.value = ' state'
        mock_header_cell9 = mock.Mock()
        mock_header_cell9.value = ' city'
        mock_header_cell10 = mock.Mock()
        mock_header_cell10.value = 'zip code'
        mock_header_cell11 = mock.Mock()
        mock_header_cell11.value = 'address'
        mock_header_cell12 = mock.Mock()
        mock_header_cell12.value = 'related user'
        mock_client_type_cell = mock.Mock()
        mock_client_type_cell.value = 'some type here'
        mock_client_name_cell = mock.Mock()
        mock_client_name_cell.value = 'client name whatever'
        mock_client_id_cell = mock.Mock()
        mock_client_id_cell.value = '123 4568'
        mock_client_email_cell = mock.Mock()
        mock_client_email_cell.value = 'email@valid.id'
        mock_client_phone_cell = mock.Mock()
        mock_client_phone_cell.value = '132456888'
        mock_client_mobile_cell = mock.Mock()
        mock_client_mobile_cell.value = ''
        mock_client_country_cell = mock.Mock()
        mock_client_country_cell.value = ''
        mock_client_state_cell = mock.Mock()
        mock_client_state_cell.value = 'Flirida'
        mock_client_city_cell = mock.Mock()
        mock_client_city_cell.value = 'some city'
        mock_client_zip_cell = mock.Mock()
        mock_client_zip_cell.value = '4545454'
        mock_client_address_cell = mock.Mock()
        mock_client_address_cell.value = '4545454'
        mock_client_user_cell = mock.Mock()
        mock_client_user_cell.value = 'user1'

        mock_sheet.cell.side_effect = [mock_header_cell1, mock_header_cell2, mock_header_cell3, mock_header_cell4, mock_header_cell5,
                                       mock_header_cell6, mock_header_cell7, mock_header_cell8, mock_header_cell9, mock_header_cell10,
                                       mock_header_cell11, mock_header_cell12, mock_client_type_cell, mock_client_name_cell,
                                       mock_client_id_cell, mock_client_email_cell, mock_client_phone_cell, mock_client_mobile_cell,
                                       mock_client_country_cell, mock_client_state_cell, mock_client_city_cell, mock_client_zip_cell,
                                       mock_client_address_cell, mock_client_user_cell]
        mock_sheet.ncols = len(IMPORT_CLIENT_EXCEL_HEADERS)
        mock_sheet.nrows = 2
        mock_book.sheet_by_index.return_value = mock_sheet
        mock_open_workbook.return_value = mock_book

        result = upload_import_client(mock_import_file, self.mock_user)

        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 5)
        self.assertEqual(mock_client_class.objects.bulk_create.call_count, 0)
        self.assertEqual(mock_save_import_history.call_count, 0)

    @mock.patch("sundog.services.open_workbook")
    @mock.patch("sundog.services.check_client_type_exists")
    @mock.patch("sundog.services.check_client_exists")
    @mock.patch("sundog.services.check_client_exists_by_identification")
    @mock.patch("sundog.services.check_username_exists")
    @mock.patch("sundog.services.save_import_history")
    @mock.patch("sundog.services.Client")
    def test_upload_import_client_headers_no_row_errors(self, mock_client_class, mock_save_import_history, mock_username_exists, mock_client_exists_by_id, mock_client_exists, mock_client_type_exists, mock_open_workbook):
        mock_client_class.objects.bulk_create.return_value = None
        mock_save_import_history.return_value = None
        mock_username_exists.return_value = None
        mock_client_exists_by_id.return_value = 1
        mock_client_exists.return_value = 1
        mock_client_type_exists.return_value = None
        mock_import_file = mock.Mock()
        mock_import_file.read.return_value = []
        mock_book = mock.Mock()
        mock_sheet = mock.Mock()
        mock_header_cell1 = mock.Mock()
        mock_header_cell1.value = 'client type'
        mock_header_cell2 = mock.Mock()
        mock_header_cell2.value = 'client name'
        mock_header_cell3 = mock.Mock()
        mock_header_cell3.value = 'identification '
        mock_header_cell4 = mock.Mock()
        mock_header_cell4.value = 'email'
        mock_header_cell5 = mock.Mock()
        mock_header_cell5.value = ' phone number'
        mock_header_cell6 = mock.Mock()
        mock_header_cell6.value = ' mobile number'
        mock_header_cell7 = mock.Mock()
        mock_header_cell7.value = ' country'
        mock_header_cell8 = mock.Mock()
        mock_header_cell8.value = ' state'
        mock_header_cell10 = mock.Mock()
        mock_header_cell10.value = 'zip code'
        mock_header_cell11 = mock.Mock()
        mock_header_cell11.value = 'address'
        mock_header_cell12 = mock.Mock()
        mock_header_cell12.value = 'related user'

        mock_sheet.cell.side_effect = [mock_header_cell1, mock_header_cell2, mock_header_cell3, mock_header_cell4, mock_header_cell5,
                                       mock_header_cell6, mock_header_cell7, mock_header_cell8, mock_header_cell10,
                                       mock_header_cell11, mock_header_cell12]
        mock_sheet.ncols = len(IMPORT_CLIENT_EXCEL_HEADERS) - 1
        mock_sheet.nrows = 1
        mock_book.sheet_by_index.return_value = mock_sheet
        mock_open_workbook.return_value = mock_book

        result = upload_import_client(mock_import_file, self.mock_user)

        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 6)
        self.assertEqual(mock_client_class.objects.bulk_create.call_count, 0)
        self.assertEqual(mock_save_import_history.call_count, 0)

if __name__ == '__main__':
    unittest.main()
