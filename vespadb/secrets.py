import os
import boto3
import json
from typing import Optional, Dict, Any
from botocore.exceptions import NoCredentialsError
import logging

logger = logging.getLogger(__name__)

def get_secret(secret_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve secret from AWS Secrets Manager

    Args:
    secret_name (str): The name of the secret to retrieve.

    Returns:
    Optional[Dict[str, Any]]: A dictionary of the secret key-value pairs if successful, None otherwise.
    """
    region_name = "us-east-1"  # specify the AWS region of the Secrets Manager

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except NoCredentialsError:
        logger.exception("Credentials not available")
        return None
    else:
        secret = get_secret_value_response['SecretString']
        return json.loads(secret)  # type: ignore[no-any-return]
