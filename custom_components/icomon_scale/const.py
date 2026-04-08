DOMAIN = "icomon_scale"

CONF_MAC = "mac_address"
CONF_NUM_USERS = "num_users"
CONF_USERS = "users"
CONF_USER_NAME = "user_name"
CONF_HEIGHT = "height"
CONF_AGE = "age"
CONF_GENDER = "gender"

DEFAULT_POLL_INTERVAL = 5
DEFAULT_TIMEOUT = 60

# Impedance conversion: raw_value / FACTOR = impedance in Ohms
# Calibrated: raw=3285 => ~594 Ohm => fat=19.1%
IMP_CONVERSION = 5.532
