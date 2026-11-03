"""Physics and layout constants shared by simulation, tools and tests.

Values are in *world units* (u). The reference camera shows 960 × 540 u, which
maps to 1920 × 1080 pixels at the reference resolution (2 px per unit) and to
3840 × 2160 at 4K. Movement constants were ported unchanged from the
TypeScript edition so the fifteen legacy levels keep their tuned jumps.
"""

FIXED_DT = 1 / 120
MAX_FRAME_DT = 0.25

GRAVITY = 1550.0
JUMP_SPEED = 590.0
JUMP_CUT_SPEED = -190.0  # releasing jump clamps upward speed to this value
MAX_FALL_SPEED = 850.0
WALK_SPEED = 220.0
RUN_SPEED = 340.0
GROUND_ACCEL = 1400.0
AIR_ACCEL = 1000.0
GROUND_FRICTION = 1500.0
ICE_FRICTION = 180.0
AIR_DRAG = 500.0
COYOTE_TIME = 0.1
JUMP_BUFFER = 0.12
STOMP_BOUNCE = 390.0

PLAYER_WIDTH = 22.0
PLAYER_SMALL_HEIGHT = 30.0
PLAYER_BIG_HEIGHT = 46.0

VIEW_WIDTH = 960.0
VIEW_HEIGHT = 540.0

# Swimming (Costa dos Corais and other water volumes).
WATER_GRAVITY = 420.0
WATER_MAX_FALL = 150.0
WATER_SWIM_IMPULSE = 230.0
WATER_MAX_SPEED = 150.0
WATER_ACCEL = 600.0
WATER_DRAG = 380.0

COIN_SIZE = (16.0, 20.0)
RELIC_SIZE = (22.0, 24.0)
ITEM_SIZE = 24.0

LIVES_START = 5
LIVES_MAX = 99
COINS_PER_LIFE = 100
STAR_DURATION = 12.0
