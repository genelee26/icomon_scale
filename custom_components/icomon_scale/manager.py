import logging
import asyncio
from datetime import timedelta
from bleak import BleakClient
from homeassistant.components.bluetooth import (
    async_register_callback,
    async_ble_device_from_address,
    BluetoothServiceInfoBleak,
    BluetoothScanningMode,
    BluetoothChange,
)
from homeassistant.helpers.event import async_track_time_interval, async_call_later
from .const import (
    CONF_MAC, CONF_USERS, CONF_USER_NAME, CONF_HEIGHT, CONF_AGE, CONF_GENDER,
    IMP_CONVERSION, DEFAULT_POLL_INTERVAL, DEFAULT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class IcomonManager:
    def __init__(self, hass, config_entry):
        self.hass = hass
        self.mac = config_entry.data[CONF_MAC]
        self.users = config_entry.data[CONF_USERS]
        self._user_entities = {}
        self._active_user = None
        self._is_connecting = False
        self._poll_unsub = None
        self._timeout_unsub = None
        self._ble_unsub = None
        self._stable_buffer = []
        self._lock_event = asyncio.Event()

    def register_user_entities(self, user_index, entities_dict):
        self._user_entities[user_index] = entities_dict

    def setup_ble_callback(self):
        """Register BLE callback once at startup (always listening, only acts when active)."""
        self._ble_unsub = async_register_callback(
            self.hass, self._handle_ble_event,
            {"address": self.mac},
            BluetoothScanningMode.ACTIVE,
        )

    def _handle_ble_event(self, service_info: BluetoothServiceInfoBleak, change: BluetoothChange):
        if self._active_user is not None and not self._is_connecting:
            _LOGGER.debug("ICOMON: BLE callback triggered, starting connect")
            self.hass.async_create_task(self._connect())

    async def start_measurement(self, user_index):
        if self._active_user is not None:
            _LOGGER.warning("ICOMON: measurement in progress for user %d, rejecting user %d",
                            self._active_user, user_index)
            return False

        self._active_user = user_index
        self._stable_buffer = []
        self._lock_event.clear()
        self._is_connecting = False

        entities = self._user_entities.get(user_index, {})
        status = entities.get("status")
        if status:
            status.update_val("等待上秤...")

        _LOGGER.warning("ICOMON: measurement started for user %d (%s)",
                        user_index, self.users[user_index].get(CONF_USER_NAME, ""))

        self._poll_unsub = async_track_time_interval(
            self.hass, self._poll_check, timedelta(seconds=DEFAULT_POLL_INTERVAL)
        )
        self._timeout_unsub = async_call_later(
            self.hass, DEFAULT_TIMEOUT, self._on_timeout
        )
        return True

    async def _poll_check(self, now=None):
        if self._active_user is None or self._is_connecting:
            return
        ble_device = async_ble_device_from_address(self.hass, self.mac, connectable=True)
        if ble_device:
            _LOGGER.debug("ICOMON: poll found connectable device")
            await self._connect()

    async def _on_timeout(self, now=None):
        if self._active_user is not None:
            entities = self._user_entities.get(self._active_user, {})
            status = entities.get("status")
            if status:
                status.update_val("超时")
            _LOGGER.warning("ICOMON: measurement timeout for user %d", self._active_user)
        self._stop_measurement()

    def _stop_measurement(self):
        if self._poll_unsub:
            self._poll_unsub()
            self._poll_unsub = None
        if self._timeout_unsub:
            self._timeout_unsub()
            self._timeout_unsub = None
        self._active_user = None
        self._is_connecting = False

    def stop(self):
        self._stop_measurement()
        if self._ble_unsub:
            self._ble_unsub()
            self._ble_unsub = None

    async def _connect(self):
        if self._is_connecting or self._active_user is None:
            return
        self._is_connecting = True
        self._stable_buffer = []
        self._lock_event.clear()
        client = None

        entities = self._user_entities.get(self._active_user, {})
        status = entities.get("status")

        try:
            ble_device = async_ble_device_from_address(self.hass, self.mac, connectable=True)
            if not ble_device:
                _LOGGER.warning("ICOMON: no connectable device")
                self._is_connecting = False
                return

            if status:
                status.update_val("连接中...")
            client = BleakClient(ble_device)
            await client.connect(timeout=15.0)

            if client.is_connected:
                target_char = None
                write_char = None
                for s in client.services:
                    for c in s.characteristics:
                        if "notify" in c.properties:
                            target_char = c.uuid
                        if "write" in c.properties or "write-without-response" in c.properties:
                            write_char = c.uuid

                if target_char:
                    await client.start_notify(target_char, self._handler)
                    if write_char:
                        await client.write_gatt_char(
                            write_char, bytes.fromhex("FD37000000000000"), response=False
                        )
                    try:
                        await asyncio.wait_for(self._lock_event.wait(), timeout=25.0)
                    except asyncio.TimeoutError:
                        _LOGGER.warning("ICOMON: no stable reading within GATT session")

        except Exception as e:
            _LOGGER.error("ICOMON: connection error: %s", e)
        finally:
            if client and client.is_connected:
                try:
                    await client.disconnect()
                except Exception:
                    pass

            if self._lock_event.is_set():
                # Measurement succeeded
                if status:
                    status.update_val("已完成")
                await asyncio.sleep(5)
                self._stop_measurement()
            else:
                # Connection failed or no stable data, allow retry
                self._is_connecting = False
                if status:
                    status.update_val("等待上秤...")

    def _handler(self, sender, data):
        if self._active_user is None:
            return

        if len(data) >= 6 and data[0] == 0xAC:
            val_int = (data[3] << 16) | (data[4] << 8) | data[5]
            weight_kg = (val_int - 9175040) / 1000.0
            raw_imp = (data[17] << 8) | data[18] if len(data) > 18 else 0

            if weight_kg > 2.0:
                entities = self._user_entities.get(self._active_user, {})
                weight_ent = entities.get("weight")
                status_ent = entities.get("status")
                if weight_ent:
                    weight_ent.update_val(round(weight_kg, 2))
                if status_ent:
                    status_ent.update_val("称重中")

                self._stable_buffer.append(weight_kg)
                if len(self._stable_buffer) > 3:
                    self._stable_buffer.pop(0)
                if (len(self._stable_buffer) == 3
                        and max(self._stable_buffer) - min(self._stable_buffer) < 0.05):
                    self._calculate(weight_kg, raw_imp)
                    self._lock_event.set()

    def _calculate(self, weight, raw_imp):
        if self._active_user is None:
            return

        user = self.users[self._active_user]
        entities = self._user_entities.get(self._active_user, {})

        h = user[CONF_HEIGHT]
        age = user[CONF_AGE]
        is_male = user[CONF_GENDER] == "male"

        impedance = raw_imp / IMP_CONVERSION if raw_imp > 0 else 500.0
        bmi = weight / ((h / 100) ** 2)

        # LBM coefficient
        lbm_coeff = ((h * 9.058 / 100) * (h / 100)
                     + weight * 0.32 + 12.226
                     - impedance * 0.0068
                     - age * 0.0542)

        # Body fat %
        if is_male:
            fat_const = 0.8
            fat_coeff = 1.0
            if weight < 61:
                fat_coeff = 0.98
            if h > 160:
                fat_coeff *= 1.03
        else:
            fat_const = 9.25 if age <= 49 else 7.25
            fat_coeff = 1.0
            if weight > 60:
                fat_coeff = 0.96
            elif weight < 50:
                fat_coeff = 1.02
            if h > 160:
                fat_coeff *= 1.03

        fat_pct = (1.0 - (((lbm_coeff - fat_const) * fat_coeff) / weight)) * 100
        fat_pct = max(3.0, min(60.0, fat_pct))

        # Water %
        water_pct = (100 - fat_pct) * 0.7
        water_coeff = 1.02 if water_pct <= 50 else 0.98
        water_pct = max(35, min(75, water_pct * water_coeff))

        # Bone mass -> bone rate %
        if is_male:
            bone_mass = (0.18016894 - (lbm_coeff * 0.05158)) * -1
        else:
            bone_mass = (0.245691014 - (lbm_coeff * 0.07158)) * -1
        if bone_mass > 2.2:
            bone_mass += 0.1
        else:
            bone_mass -= 0.1
        bone_mass = max(0.5, bone_mass)
        bone_pct = round(bone_mass * 0.85 / weight * 100, 1)

        # Muscle
        fat_mass = fat_pct * 0.01 * weight
        muscle_mass = weight - fat_mass - bone_mass * 0.85
        muscle_rate = round(muscle_mass / weight * 100, 1)
        skeletal_muscle = round(muscle_mass / weight * 100 * 0.558, 1)

        # Protein %
        protein_pct = round(muscle_mass / weight * 100 - water_pct, 1)
        protein_pct = max(5, min(32, protein_pct))

        # FFM
        ffm = round(weight - fat_mass, 1)

        # BMR (Mifflin-St Jeor)
        if is_male:
            bmr = round(10 * weight + 6.25 * h - 5 * age + 5)
        else:
            bmr = round(10 * weight + 6.25 * h - 5 * age - 161)

        # Visceral fat
        visceral_fat = round(bmi * 0.5 - age * 0.05 + 0.4, 1)
        visceral_fat = max(1.0, min(50.0, visceral_fat))

        # Subcutaneous fat
        subcut_fat = round(fat_pct * 0.71, 1)

        # Physique
        if bmi < 18.5:
            physique = "偏瘦"
        elif bmi < 24:
            physique = "标准"
        elif bmi < 28:
            physique = "超重"
        else:
            physique = "肥胖"

        # Update entities
        updates = {
            "bmi": round(bmi, 1),
            "body_fat": round(fat_pct, 1),
            "water": round(water_pct, 1),
            "skeletal_muscle": skeletal_muscle,
            "bone": bone_pct,
            "protein": protein_pct,
            "muscle_rate": muscle_rate,
            "visceral_fat": visceral_fat,
            "subcutaneous_fat": subcut_fat,
            "ffm": ffm,
            "bmr": bmr,
            "physique": physique,
            "impedance": round(impedance, 1),
            "status": "已锁定",
        }
        for key, val in updates.items():
            ent = entities.get(key)
            if ent:
                ent.update_val(val)

        _LOGGER.warning(
            "ICOMON: LOCKED user=%s w=%.2f Z=%.0f fat=%.1f water=%.1f bmr=%d",
            user.get(CONF_USER_NAME, "?"), weight, impedance, fat_pct, water_pct, bmr
        )
