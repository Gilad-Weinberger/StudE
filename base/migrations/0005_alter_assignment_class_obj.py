# Generated by Django 4.1.13 on 2024-12-11 07:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_alter_assignment_class_obj_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='class_obj',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.class'),
        ),
    ]