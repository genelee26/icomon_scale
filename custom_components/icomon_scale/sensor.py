from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    RestoreSensor,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import UnitOfMass, EntityCategory, PERCENTAGE
from homeassistant.util import slugify
from .const import DOMAIN, CONF_MAC, CONF_USERS, CONF_USER_NAME


async def async_setup_entry(hass, config_entry, async_add_entities):
    manager = hass.data[DOMAIN][config_entry.entry_id]
    mac = config_entry.data[CONF_MAC]
    users = config_entry.data[CONF_USERS]

    all_entities = []
    for idx, user in enumerate(users):
        name = user[CONF_USER_NAME]
        slug = slugify(name) or f"user{idx}"
        user_entities = _create_user_sensors(mac, name, slug)
        manager.register_user_entities(idx, user_entities)
        all_entities.extend(user_entities.values())

    async_add_entities(all_entities, False)


def _create_user_sensors(mac, user_name, slug):
    return {
        "weight": WeightSensor(mac, user_name, slug),
        "bmi": BMISensor(mac, user_name, slug),
        "body_fat": BodyFatSensor(mac, user_name, slug),
        "water": WaterSensor(mac, user_name, slug),
        "skeletal_muscle": SkeletalMuscleSensor(mac, user_name, slug),
        "bone": BoneSensor(mac, user_name, slug),
        "protein": ProteinSensor(mac, user_name, slug),
        "muscle_rate": MuscleRateSensor(mac, user_name, slug),
        "visceral_fat": VisceralFatSensor(mac, user_name, slug),
        "subcutaneous_fat": SubcutaneousFatSensor(mac, user_name, slug),
        "ffm": FFMSensor(mac, user_name, slug),
        "bmr": BMRSensor(mac, user_name, slug),
        "physique": PhysiqueSensor(mac, user_name, slug),
        "impedance": ImpedanceSensor(mac, user_name, slug),
        "status": StatusSensor(mac, user_name, slug),
    }


class BaseSensor(RestoreSensor):
    # Subclasses with transient state (e.g. measurement progress strings)
    # should set this to False so they reset to unknown across restarts
    # instead of resurrecting a stale "称重中" / "等待上秤..." value.
    _restore_state = True

    def __init__(self, mac, user_name, slug):
        self._mac = mac
        self._user_name = user_name
        self._slug = slug
        self._state = None
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mac)},
            name="Icomon 智能体脂秤",
            manufacturer="Icomon",
            model="Smart Scale",
        )

    @property
    def native_value(self):
        return self._state

    def update_val(self, val):
        self._state = val
        if self.hass and self.entity_id:
            self.schedule_update_ha_state()

    async def async_added_to_hass(self) -> None:
        # On-demand measurement devices have no value between sessions; without
        # this restoration each HA restart resets state to None → HA statistics
        # module drops the entity from its tracking list and stops generating
        # hourly aggregates until the next manual measurement.
        await super().async_added_to_hass()
        if not self._restore_state:
            return
        if self.state_class is not None:
            last_data = await self.async_get_last_sensor_data()
            if last_data is not None and last_data.native_value is not None:
                self._state = last_data.native_value
                return
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (None, "unknown", "unavailable", ""):
            self._state = last_state.state


class WeightSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 体重"
        self._attr_unique_id = f"{mac}_{slug}_weight"
        self._attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
        self._attr_device_class = SensorDeviceClass.WEIGHT
        self._attr_state_class = SensorStateClass.MEASUREMENT


class BMISensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} BMI"
        self._attr_unique_id = f"{mac}_{slug}_bmi"
        self._attr_icon = "mdi:human"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class BodyFatSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 体脂率"
        self._attr_unique_id = f"{mac}_{slug}_fat"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:percent"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class WaterSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 水分率"
        self._attr_unique_id = f"{mac}_{slug}_water"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:water-percent"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class SkeletalMuscleSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 骨骼肌率"
        self._attr_unique_id = f"{mac}_{slug}_skeletal_muscle"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:arm-flex"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class BoneSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 骨骼率"
        self._attr_unique_id = f"{mac}_{slug}_bone"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:bone"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class ProteinSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 蛋白质率"
        self._attr_unique_id = f"{mac}_{slug}_protein"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:food-steak"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class MuscleRateSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 肌肉率"
        self._attr_unique_id = f"{mac}_{slug}_muscle_rate"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:arm-flex-outline"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class VisceralFatSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 内脏脂肪指数"
        self._attr_unique_id = f"{mac}_{slug}_visceral_fat"
        self._attr_icon = "mdi:stomach"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class SubcutaneousFatSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 皮下脂肪率"
        self._attr_unique_id = f"{mac}_{slug}_subcutaneous_fat"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:layers"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class FFMSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 去脂体重"
        self._attr_unique_id = f"{mac}_{slug}_ffm"
        self._attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
        self._attr_icon = "mdi:scale-bathroom"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class BMRSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 基础代谢"
        self._attr_unique_id = f"{mac}_{slug}_bmr"
        self._attr_native_unit_of_measurement = "kcal"
        self._attr_icon = "mdi:fire"
        self._attr_state_class = SensorStateClass.MEASUREMENT


class ImpedanceSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 阻抗"
        self._attr_unique_id = f"{mac}_{slug}_impedance"
        self._attr_native_unit_of_measurement = "Ω"
        self._attr_icon = "mdi:flash"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC


class PhysiqueSensor(BaseSensor):
    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 身材评价"
        self._attr_unique_id = f"{mac}_{slug}_physique"
        self._attr_icon = "mdi:human-handsup"


class StatusSensor(BaseSensor):
    _restore_state = False

    def __init__(self, mac, user_name, slug):
        super().__init__(mac, user_name, slug)
        self._attr_name = f"{user_name} 测量状态"
        self._attr_unique_id = f"{mac}_{slug}_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:bluetooth-connect"
