from django.db import migrations


def forwards(apps, schema_editor):
    MemberSequence = apps.get_model("members", "MemberSequence")
    MemberSequence.objects.get_or_create(id=1, defaults={"last_value": 0})


def backwards(apps, schema_editor):
    MemberSequence = apps.get_model("members", "MemberSequence")
    MemberSequence.objects.filter(id=1).delete()


class Migration(migrations.Migration):
    dependencies = [("members", "0001_initial")]
    operations = [migrations.RunPython(forwards, backwards)]
