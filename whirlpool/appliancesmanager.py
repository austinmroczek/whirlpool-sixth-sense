import json
import logging

import aiohttp

from .auth import Auth
from .backendselector import BackendSelector

LOGGER = logging.getLogger(__name__)


class AppliancesManager:
    def __init__(
        self,
        backend_selector: BackendSelector,
        auth: Auth,
        session: aiohttp.ClientSession,
    ):
        self._backend_selector = backend_selector
        self._auth = auth
        self._aircons = None
        self._washer_dryers = None
        self._ovens = None
        self._session: aiohttp.ClientSession = session

    def _create_headers(self):
        return {
            "Authorization": "Bearer " + self._auth.get_access_token(),
            "Content-Type": "application/json",
            # "Host": "api.whrcloud.eu",
            "User-Agent": "okhttp/3.12.0",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

    async def fetch_appliances(self):
        account_id = None
        async with self._session.get(
            f"{self._backend_selector.base_url}/api/v1/getUserDetails",
            headers=self._create_headers(),
        ) as r:
            if r.status != 200:
                LOGGER.error(f"Failed to get account id: {r.status}")
                return False
            account_id = json.loads(await r.text())["accountId"]

        async with self._session.get(
            f"{self._backend_selector.base_url}/api/v2/appliance/all/account/{account_id}",
            headers=self._create_headers(),
        ) as r:
            if r.status != 200:
                LOGGER.error(f"Failed to get appliances: {r.status}")
                return False

            self._aircons = []
            self._washer_dryers = []
            self._ovens = []

            locations = json.loads(await r.text())[str(account_id)]
            for appliances in locations.values():
                for appliance in appliances:
                    appliance_data = {
                        "SAID": appliance["SAID"],
                        "NAME": appliance["APPLIANCE_NAME"],
                        "DATA_MODEL": appliance["DATA_MODEL_KEY"],
                        "CATEGORY": appliance["CATEGORY_NAME"],
                        "MODEL_NUMBER": appliance.get("MODEL_NO"),
                        "SERIAL_NUMBER": appliance.get("SERIAL"),
                    }
                    data_model = appliance["DATA_MODEL_KEY"].lower()
                    if "airconditioner" in data_model:
                        self._aircons.append(appliance_data)
                    elif "dryer" in data_model or "washer" in data_model:
                        self._washer_dryers.append(appliance_data)
                    elif "cooking_minerva" in data_model or "cooking_vsi" in data_model:
                        self._ovens.append(appliance_data)
                    else:
                        LOGGER.warning(
                            "Unsupported appliance data model %s", data_model
                        )
        return True

    @property
    def aircons(self):
        return self._aircons

    @property
    def washer_dryers(self):
        return self._washer_dryers

    @property
    def ovens(self):
        return self._ovens
