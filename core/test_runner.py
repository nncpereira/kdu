from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.test.runner import DiscoverRunner


class ProjectAppsDiscoverRunner(DiscoverRunner):
    """
    ``manage.py test`` with no labels defaults to unittest's directory-walk
    discovery starting at BASE_DIR, which descends into .venv/ (nested
    inside BASE_DIR) and imports unrelated third-party test modules as a
    side effect. That has been observed to leave django.db.connections
    with a DATABASES alias whose TEST dict is missing defaults (e.g.
    "MIRROR"), crashing setup_databases with a bare KeyError. Default
    instead to discovering only this project's own installed apps —
    those living directly under BASE_DIR, as opposed to django.contrib.*
    or third-party packages installed under .venv — matching
    ``manage.py test <app1> <app2> ...`` explicitly.
    """

    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            test_labels = [
                config.label
                for config in apps.get_app_configs()
                if Path(config.path).parent == settings.BASE_DIR
            ]
        return super().build_suite(test_labels, **kwargs)
