"""Aws Secrets Manager helper functions."""

import json
import logging
from typing import Any

import boto3
from botocore.exceptions import NoCredentialsError

logger = logging.getLogger(__name__)


def get_secret(secret_name: str) -> dict[str, Any] | None:
    """Retrieve secret from AWS Secrets Manager.

    Args:
    secret_name (str): The name of the secret to retrieve.

    Returns
    -------
    Optional[Dict[str, Any]]: A dictionary of the secret key-value pairs if successful, None otherwise.
    """
    region_name = "us-east-1"  # specify the AWS region of the Secrets Manager

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except NoCredentialsError:
        logger.exception("Credentials not available")
        return None
    else:
        secret = get_secret_value_response["SecretString"]
        return json.loads(secret)  # type: ignore[no-any-return]
