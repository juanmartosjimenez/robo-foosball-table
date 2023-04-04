import math
from collections import deque

BALL_MASS = 24  # mass of ball
FRICTION_COEFF = 0.3  # coefficient of friction
RESTIT_COEFF = 0.9  # coefficient of restitution
GRAVITY = 9.81

def calculate_forces(vx, vy, x, y, radius, top, bottom):
    """Calculate the forces acting on the ball at a given time step."""
    # Gravity force
    F_gravity_x = 0
    F_gravity_y = 0

    # Friction force
    if vx > 0:
        F_friction_x = -FRICTION_COEFF * BALL_MASS * GRAVITY
    else:
        F_friction_x = FRICTION_COEFF * BALL_MASS * GRAVITY
    F_friction_y = 0

    # Wall collision force
    if y + radius >= top:
        F_collision_y = -RESTIT_COEFF * abs(vy)
    elif y - radius <= bottom:
        F_collision_y = RESTIT_COEFF * abs(vy)
    else:
        F_collision_y = 0
    F_collision_x = 0

    # Calculate total forces
    F_total_x = F_gravity_x + F_friction_x + F_collision_x
    F_total_y = F_gravity_y + F_friction_y + F_collision_y

    return F_total_x, F_total_y


# Simulate the motion of the ball
def calculate_end_pos(prev_center_pts: deque[tuple[int, float]], fps: int, radius: int, top_y: float, bottom_y: float, goal_x: float):
    frames = [x for x in prev_center_pts]
    if len(prev_center_pts) > 1:
        dt = 2 / fps
        # reverse top and bottom because 0 is the top
        top = bottom_y
        bottom = top_y

        x = prev_center_pts[-1][0]
        y = frames[-1][1]
        vx = (x - frames[-2][0]) / dt
        vy = (y - frames[-2][1]) / dt

        stop_thresh = 50
        if vx < stop_thresh or vx < 0:
            return y

        while x < goal_x:
        # Calculate forces
            F_total_x, F_total_y = calculate_forces(vx, vy, x, y, radius, top, bottom)

            # Update velocity
            vx += F_total_x / BALL_MASS * dt
            vy += F_total_y / BALL_MASS * dt


            if vx < stop_thresh or vx < 0:
                return frames[-1][1]

            # Update position
            x += vx * dt
            y += vy * dt
        return y

            

# Print the final position of the ball