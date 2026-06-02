import sys
from types import SimpleNamespace

from app import config


def test_load_aws_parameter_values_reads_parameter_path(monkeypatch):
    calls = []

    class FakeSsmClient:
        def get_parameters_by_path(self, **kwargs):
            calls.append(kwargs)
            return {
                "Parameters": [
                    {"Name": "/gamerec/prod/DATABASE_URL", "Value": "postgres-url"},
                    {"Name": "/gamerec/prod/SECRET_KEY", "Value": "secret"},
                    {"Name": "/gamerec/prod/nested/rawg_api_key", "Value": "rawg"},
                ]
            }

    fake_boto3 = SimpleNamespace(client=lambda service, region_name: FakeSsmClient())
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setenv("AWS_SSM_PARAMETER_PATH", "/gamerec/prod")
    monkeypatch.setenv("AWS_REGION", "ap-southeast-1")

    values = config._load_aws_parameter_values()

    assert values == {
        "DATABASE_URL": "postgres-url",
        "SECRET_KEY": "secret",
        "NESTED_RAWG_API_KEY": "rawg",
    }
    assert calls == [
        {
            "Path": "/gamerec/prod",
            "Recursive": True,
            "WithDecryption": True,
        }
    ]
