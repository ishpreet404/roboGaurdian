#include "odometry.h"

#include <math.h>

void odomInit(OdomState *state)
{
    if (!state)
    {
        return;
    }
    state->x = 0.0f;
    state->y = 0.0f;
    state->distance_m = 0.0f;
    state->speed_mps = 0.0f;
    state->heading_deg = 0.0f;
}

void odomUpdate(OdomState *state, float speed_mps, float heading_deg, float dt)
{
    if (!state || dt <= 0.0f)
    {
        return;
    }
    state->speed_mps = speed_mps;
    state->heading_deg = heading_deg;

    float heading_rad = heading_deg * 0.0174533f;
    float dx = cosf(heading_rad) * speed_mps * dt;
    float dy = sinf(heading_rad) * speed_mps * dt;

    state->x += dx;
    state->y += dy;
    state->distance_m += fabsf(speed_mps) * dt;
}
