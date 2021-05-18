import hvac
from st2common.runners.base_action import Action


class VaultBaseAction(Action):

    def __init__(self, config):
        super(VaultBaseAction, self).__init__(config)
        self.vault = self._get_client()

    def _get_client(self):
        url = self.config['url']
        verify = self._get_verify()

        auth_method = self.config.get("auth_method", "token")
        token = self.config["token"]

        # token is passed during client init to allow client to also
        # get the token from VAULT_TOKEN env var or ~/.vault-token
        client = hvac.Client(url=url, token=token, verify=verify)

        # NB: for auth_methods, we used to be able to login with
        # client.auth_*, but most of those have been deprecated
        # in favor of: client.auth.<method>.login
        # So, use client.auth.<method> where implemented

        # Support for optional kwargs - only passed to login method if defined in config
        login_kwargs = {}

        auth_mount_point = self.config.get("auth_mount_point")
        if auth_mount_point:
            login_kwargs["mount_point"] = auth_mount_point

        # token is handled during client init
        # other auth methods will override it as needed
        if auth_method == "token":
            pass
        elif auth_method == "approle":
            client.auth.approle.login(
                role_id=self.config["role_id"],
                secret_id=self.config["secret_id"],
                **login_kwargs,
            )
        elif auth_method == "kubernetes":
            with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as sa_token:
                client.auth.kubernetes.login(
                    self.config["role"],
                    sa_token.read(),
                    **login_kwargs,
                )
        else:
            raise NotImplementedError(
                "The {} auth method has a typo or has not been implemented (yet).".format(
                    auth_method
                )
            )

        return client

    def _get_verify(self):
        verify = self.config['verify']
        cert = self.config['cert']
        if verify and cert:
            return cert
        return verify
