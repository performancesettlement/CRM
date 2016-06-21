from services import get_access_file_history


def recent_files(request):
    return {'recent_files': get_access_file_history(request.user)}
