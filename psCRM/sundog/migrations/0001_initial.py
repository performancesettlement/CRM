# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailcore.fields
from django.conf import settings
import django.core.validators
import sundog.utils


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wagtailcore', '0019_verbose_names_cleanup'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('client_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('last_name', models.CharField(max_length=100, null=True, blank=True)),
                ('identification', models.CharField(unique=True, max_length=100)),
                ('email', models.CharField(max_length=100, null=True, blank=True)),
                ('phone_number', models.CharField(max_length=50, null=True, blank=True)),
                ('mobile_number', models.CharField(max_length=50, null=True, blank=True)),
                ('country', models.CharField(max_length=60, null=True, blank=True)),
                ('state', models.CharField(blank=True, max_length=4, null=True, choices=[(b'AL', 'Alabama'), (b'AK', 'Alaska'), (b'AZ', 'Arizona'), (b'AR', 'Arkansas'), (b'CA', 'California'), (b'CO', 'Colorado'), (b'CT', 'Connecticut'), (b'DE', 'Delaware'), (b'DC', 'District of Columbia'), (b'FL', 'Florida'), (b'GA', 'Georgia'), (b'HI', 'Hawaii'), (b'ID', 'Idaho'), (b'IL', 'Illinois'), (b'IN', 'Indiana'), (b'IA', 'Iowa'), (b'KS', 'Kansas'), (b'KY', 'Kentucky'), (b'LA', 'Louisiana'), (b'ME', 'Maine'), (b'MD', 'Maryland'), (b'MA', 'Massachusetts'), (b'MI', 'Michigan'), (b'MN', 'Minnesota'), (b'MS', 'Mississippi'), (b'MO', 'Missouri'), (b'MT', 'Montana'), (b'NE', 'Nebraska'), (b'NV', 'Nevada'), (b'NH', 'New Hampshire'), (b'NJ', 'New Jersey'), (b'NM', 'New Mexico'), (b'NY', 'New York'), (b'NC', 'North Carolina'), (b'ND', 'North Dakota'), (b'OH', 'Ohio'), (b'OK', 'Oklahoma'), (b'OR', 'Oregon'), (b'PA', 'Pennsylvania'), (b'RI', 'Rhode Island'), (b'SC', 'South Carolina'), (b'SD', 'South Dakota'), (b'TN', 'Tennessee'), (b'TX', 'Texas'), (b'UT', 'Utah'), (b'VT', 'Vermont'), (b'VA', 'Virginia'), (b'WA', 'Washington'), (b'WV', 'West Virginia'), (b'WI', 'Wisconsin'), (b'WY', 'Wyoming')])),
                ('city', models.CharField(max_length=60, null=True, blank=True)),
                ('zip_code', models.CharField(max_length=12, null=True, blank=True)),
                ('address', models.CharField(max_length=300, null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'permissions': (('import_clients', 'Can import clients'),),
            },
        ),
        migrations.CreateModel(
            name='ClientType',
            fields=[
                ('client_type_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Client Type',
                'verbose_name_plural': 'Client Type List',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('document', models.FileField(upload_to=sundog.utils.document_directory_path)),
            ],
        ),
        migrations.CreateModel(
            name='FileAccessHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('time', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='FileImportHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('import_file_path', models.CharField(max_length=255)),
                ('import_checksum', models.CharField(max_length=50)),
                ('user_full_name', models.CharField(max_length=100)),
                ('user_username', models.CharField(max_length=30)),
                ('import_time', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='FileStatus',
            fields=[
                ('status_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('related_color', models.CharField(blank=True, max_length=20, null=True, choices=[(b'', b'Plain Gray'), (b'label-primary', b'Green'), (b'label-information', b'Light Blue'), (b'label-success', b'Electric Blue'), (b'label-warning', b'Orange'), (b'label-danger', b'Red')])),
                ('related_percent', models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('order', models.SmallIntegerField()),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'File Status',
                'verbose_name_plural': 'File Status List',
            },
        ),
        migrations.CreateModel(
            name='FileStatusHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('previous_file_status_color', models.CharField(max_length=20, null=True, blank=True)),
                ('previous_file_status', models.CharField(max_length=100, null=True, blank=True)),
                ('new_file_status', models.CharField(max_length=100)),
                ('new_file_status_color', models.CharField(max_length=20, null=True, blank=True)),
                ('modifier_user_full_name', models.CharField(max_length=100)),
                ('modifier_user_username', models.CharField(max_length=30)),
                ('modified_time', models.DateTimeField()),
            ],
            options={
                'verbose_name': 'File History',
                'verbose_name_plural': 'File History List',
            },
        ),
        migrations.CreateModel(
            name='FileStatusStat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_stat', models.DateField()),
                ('file_status', models.CharField(max_length=100)),
                ('file_count', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.CharField(max_length=255)),
                ('time', models.DateTimeField()),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MyFile',
            fields=[
                ('file_id', models.AutoField(serialize=False, primary_key=True)),
                ('description', models.CharField(max_length=1000)),
                ('creator_user_full_name', models.CharField(max_length=100)),
                ('creator_user_username', models.CharField(max_length=30)),
                ('created_time', models.DateTimeField()),
                ('last_update_user_full_name', models.CharField(max_length=100)),
                ('last_update_user_username', models.CharField(max_length=30)),
                ('last_update_time', models.DateTimeField()),
                ('active', models.BooleanField(default=True)),
                ('priority', models.PositiveSmallIntegerField(blank=True, null=True, choices=[(4, b'Top priority'), (3, b'High priority'), (2, b'Moderate priority'), (1, b'Low priority')])),
                ('quoted_price', models.DecimalField(null=True, max_digits=12, decimal_places=2, blank=True)),
                ('quoted_date', models.DateField(null=True, blank=True)),
                ('invoice_price', models.DecimalField(null=True, max_digits=12, decimal_places=2, blank=True)),
                ('invoice_date', models.DateField(null=True, blank=True)),
                ('client', models.ForeignKey(to='sundog.Client')),
                ('current_status', models.ForeignKey(to='sundog.FileStatus')),
                ('file_status_history', models.ManyToManyField(to='sundog.FileStatusHistory')),
                ('messages', models.ManyToManyField(to='sundog.Message')),
                ('participants', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'File',
                'verbose_name_plural': 'Files',
                'permissions': (('view_all_files', 'Can view all files'), ('import_files', 'Can import files'), ('change_file_participant', 'Can add/remove participants from a file'), ('change_file_tag', 'Can add/remove tags from a file')),
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Terms',
            fields=[
                ('page_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('subtitle', wagtail.wagtailcore.fields.RichTextField(null=True)),
                ('body', wagtail.wagtailcore.fields.RichTextField()),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.AddField(
            model_name='myfile',
            name='tags',
            field=models.ManyToManyField(to='sundog.Tag'),
        ),
        migrations.AlterUniqueTogether(
            name='filestatusstat',
            unique_together=set([('date_stat', 'file_status')]),
        ),
        migrations.AddField(
            model_name='fileaccesshistory',
            name='file',
            field=models.ForeignKey(to='sundog.MyFile'),
        ),
        migrations.AddField(
            model_name='fileaccesshistory',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='document',
            name='file',
            field=models.ForeignKey(to='sundog.MyFile'),
        ),
        migrations.AddField(
            model_name='client',
            name='client_type',
            field=models.ForeignKey(to='sundog.ClientType'),
        ),
        migrations.AddField(
            model_name='client',
            name='related_user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
