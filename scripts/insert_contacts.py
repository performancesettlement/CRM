from sundog.models import Contact, LeadSource, User

user_id = User.objects.first().id

contact_data = {
    'lead_source': LeadSource.objects.first().lead_source_id,
    'call_center_representative': user_id,
    'assigned_to': user_id,
}

for i in range(1, 200):
    Contact(
        first_name='Some contact first name ' + str(i),
        last_name='Some contact last name ' + str(i),
        **contact_data,
    ).save()
