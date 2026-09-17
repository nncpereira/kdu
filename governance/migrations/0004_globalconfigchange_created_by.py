import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("governance", "0003_fix_obligatory_cap_value_shape"),
        ("users", "0002_seed_superadmin"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalconfigchange",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="proposed_config_changes",
                to="users.userprofile",
                default=None,
            ),
            preserve_default=False,
        ),
    ]
