import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vespadb.settings")

import sys
sys.path.append(os.path.abspath('/workspaces/vespadb'))

application = get_wsgi_application()
from django.core.mail import send_mail, EmailMessage

# Send an email with the Reply-To header set
email = EmailMessage(
    subject="test",
    body="test",
    from_email="vespawatch@inbo.be",  # This will appear as the sender's email address
    to=["steven.gerrits94@gmail.com"],
    headers={'Reply-To': 'vespawatch@inbo.be'}  # Ensures replies go to vespawatch@inbo.be
)
email.send()