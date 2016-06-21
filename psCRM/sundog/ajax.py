import services
from django.http.response import JsonResponse


# def areas_by_state(request):
#     areas_array = []
#     if request.is_ajax() and request.GET['state_id']:
#         areas = services.get_areas_by_state(request.GET['state_id'])
#         if areas is not None:
#             areas_array = [{'id': a.area_id, 'name': a.name}
#                            for a in areas]
#
#     return JsonResponse({'results': areas_array})
#
#
# def communities_by_area(request):
#     communities_array = []
#     if request.is_ajax() and request.GET['area_id']:
#         communities = services.get_communities_by_area(request.GET['area_id'])
#         if communities is not None:
#             communities_array = [{'id': a.community_id, 'name': a.name}
#                                  for a in communities]
#
#     return JsonResponse({'results': communities_array})


def get_completed_by_file_status(request):
    completed = 0
    if request.is_ajax() and request.GET['status_id']:
        completed = services.get_completed_by_file_status(request.GET['status_id'])

    return JsonResponse({'result': completed})
