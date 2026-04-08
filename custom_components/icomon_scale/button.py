import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import slugify
from .const import DOMAIN, CONF_MAC, CONF_USERS, CONF_USER_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    manager = hass.data[DOMAIN][config_entry.entry_id]
    mac = config_entry.data[CONF_MAC]
    users = config_entry.data[CONF_USERS]

    buttons = []
    for idx, user in enumerate(users):
        name = user[CONF_USER_NAME]
        slug = slugify(name) or f"user{idx}"
        buttons.append(IcomonMeasureButton(mac, idx, name, slug, manager))

    async_add_entities(buttons, False)


class IcomonMeasureButton(ButtonEntity):
    def __init__(self, mac, user_index, user_name, slug, manager):
        self._mac = mac
        self._user_index = user_index
        self._manager = manager
        self._attr_name = f"{user_name} 开始测量"
        self._attr_unique_id = f"{mac}_{slug}_measure"
        self._attr_icon = "mdi:scale-bathroom"
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            name="Icomon 智能体脂秤",
            manufacturer="Icomon",
            model="Smart Scale",
        )

    async def async_press(self):
        ok = await self._manager.start_measurement(self._user_index)
        if not ok:
            _LOGGER.warning("ICOMON: measurement rejected, another user is active")
