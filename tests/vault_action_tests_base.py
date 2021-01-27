from st2tests.base import BaseActionTestCase

from tests.utils import get_config_file_path
from tests.utils.hvac_integration_test_case import HvacIntegrationTestCase


class VaultActionTestCase(HvacIntegrationTestCase, BaseActionTestCase):
    dummy_pack_config = None
    secret_v1 = False
    secret_v2 = False

    # in setUp() and tearDown(), explicitly handle super()-like calls.
    #  - HvacIntegrationTestCase does not call super().
    #  - BaseActionTestCase does call super().

    def setUp(self):
        HvacIntegrationTestCase.setUp(self)
        # self.client = create_client(token=self.manager.root_token)
        # also mocks hvac.utils.warnings which we might not want.
        BaseActionTestCase.setUp(self)
        self.dummy_pack_config = self.build_dummy_pack_config()

        mounted_secrets_engines = self.client.sys.list_mounted_secrets_engines()["data"]
        # based on hvac/tests/integration_tests/v1/test_integration.py
        if "secret/" not in mounted_secrets_engines:
            self.client.enable_secret_backend(
                backend_type="kv",
                mount_point="secret",
                options=dict(version=1),
            )

        # based on hvac/tests/integration_tests/api/secrets_engins/test_kv_v*.py
        if self.secret_v1 and "kvv1/" not in mounted_secrets_engines:
            self.client.enable_secret_backend(
                backend_type="kv",
                mount_point="kvv1",
                options=dict(version=1),
            )
        if self.secret_v2 and "kvv2/" not in mounted_secrets_engines:
            self.client.enable_secret_backend(
                backend_type="kv",
                mount_point="kvv2",
                options=dict(version=2),
            )

    def tearDown(self):
        BaseActionTestCase.tearDown(self)
        HvacIntegrationTestCase.tearDown(self)
        self.dummy_pack_config = None
        if self.secret_v1:
            self.client.disable_secret_backend(mount_point="kvv1")
        if self.secret_v2:
            self.client.disable_secret_backend(mount_point="kvv2")

    def build_dummy_pack_config(self, url="https://localhost:8200"):
        # based on create_client() in hvac/tests/utils/__init__.py
        server_cert_path = get_config_file_path("server-cert.pem")

        token_result = self.client.create_token(lease="1h")
        token = token_result["auth"]["client_token"]

        dummy_pack_config = {
            "url": url,

            # pack config | relation | hvac.Client()
            # ------------|----------|--------------
            #    cert     |    !=    |     cert
            # cert+verify |    ==    |    verify
            "cert": server_cert_path,
            "verify": True,

            "auth_method": "token",

            "token": token,

            "role_id": None,
            "secret_id": None,
        }

        return dummy_pack_config

