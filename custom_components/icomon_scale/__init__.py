from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import (
    DOMAIN, CONF_MAC, CONF_NUM_USERS, CONF_USERS,
    CONF_USER_NAME, CONF_HEIGHT, CONF_AGE, CONF_GENDER,
)
from .manager import IcomonManager

PLATFORMS = ["sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    manager = IcomonManager(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    manager.setup_ble_callback()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        manager = hass.data[DOMAIN].pop(entry.entry_id, None)
        if manager:
            manager.stop()
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate v1 single-user config to v2 multi-user format."""
    if entry.version == 1:
        old = dict(entry.data)
        new_data = {
            CONF_MAC: old.get(CONF_MAC, old.get("mac_address", "")),
            CONF_NUM_USERS: 1,
            CONF_USERS: [{
                CONF_USER_NAME: "用户1",
                CONF_HEIGHT: old.get(CONF_HEIGHT, 175),
                CONF_AGE: old.get(CONF_AGE, 30),
                CONF_GENDER: old.get(CONF_GENDER, "male"),
            }],
        }
        hass.config_entries.async_update_entry(entry, data=new_data, version=2)
    return True
