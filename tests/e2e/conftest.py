from pathlib import Path

import pytest


@pytest.fixture
def browser_context_args(pytestconfig, playwright, device, base_url, _pw_artifacts_folder):
    context_args = {}
    if device:
        context_args.update(playwright.devices[device])
    if base_url:
        context_args["base_url"] = base_url
    if pytestconfig.getoption("--video") in ["on", "retain-on-failure"]:
        context_args["record_video_dir"] = _pw_artifacts_folder.name
    return {
        **context_args,
        "locale": "pt-BR",
        "viewport": {"width": 390, "height": 844},
    }


@pytest.fixture(autouse=True)
def isolated_browser_environment(settings, tmp_path):
    settings.ACCOUNT_ALLOW_REGISTRATION = True
    settings.ACCOUNT_RATE_LIMITS = {}
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.MEDIA_ROOT = Path(tmp_path) / "media"
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    }
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
