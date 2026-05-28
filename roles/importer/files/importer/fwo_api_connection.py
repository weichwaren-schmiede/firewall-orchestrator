class FwoApi:
    def __init__(
        self,
        api_uri: str,
        importer_user_name: str,
        importer_password: str,
        importer_mgm_uri: str,
        fwo_user_mgmt_api_uri: str,
    ):
        self.fwo_api_url = api_uri
        self.fwo_jwt = self.login(importer_user_name, importer_password, importer_mgm_uri)["AccessToken"]
        self.query_info = {}
        self.query_analyzer = QueryAnalyzer()
        self.fwo_user_mgmt_api_uri = fwo_user_mgmt_api_uri
