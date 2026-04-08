import voluptuous as vol
from homeassistant import config_entries
from .const import (
    DOMAIN, CONF_MAC, CONF_NUM_USERS, CONF_USERS,
    CONF_USER_NAME, CONF_HEIGHT, CONF_AGE, CONF_GENDER,
)


class IcomonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self):
        self._data = {}
        self._users = []
        self._current_user = 0
        self._num_users = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._data[CONF_MAC] = user_input[CONF_MAC].upper()
            self._num_users = user_input[CONF_NUM_USERS]
            self._data[CONF_NUM_USERS] = self._num_users
            self._users = []
            self._current_user = 0
            return await self.async_step_user_profile()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MAC, default="FF:FF:10:C7:4D:F3"): str,
                vol.Required(CONF_NUM_USERS, default=1): vol.In({
                    1: "1 人", 2: "2 人", 3: "3 人", 4: "4 人", 5: "5 人",
                }),
            }),
            description_placeholders={
                "step": "设置秤的 MAC 地址和用户数量",
            },
        )

    async def async_step_user_profile(self, user_input=None):
        if user_input is not None:
            self._users.append(user_input)
            self._current_user += 1
            if self._current_user >= self._num_users:
                self._data[CONF_USERS] = self._users
                return self.async_create_entry(
                    title=f"体脂秤 ({self._data[CONF_MAC]})",
                    data=self._data,
                )
            return await self.async_step_user_profile()

        idx = self._current_user + 1
        total = self._num_users
        return self.async_show_form(
            step_id="user_profile",
            data_schema=vol.Schema({
                vol.Required(CONF_USER_NAME, default=f"用户{idx}"): str,
                vol.Required(CONF_HEIGHT, default=175): int,
                vol.Required(CONF_AGE, default=30): int,
                vol.Required(CONF_GENDER, default="male"): vol.In({
                    "male": "男", "female": "女",
                }),
            }),
            description_placeholders={
                "step": f"用户 {idx} / {total}",
            },
        )
