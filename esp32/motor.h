#pragma once

#include <Arduino.h>

enum MotorCommand
{
    MOTOR_STOP = 0,
    MOTOR_FORWARD,
    MOTOR_BACKWARD,
    MOTOR_LEFT,
    MOTOR_RIGHT
};

void motorInit();
void motorSetCommand(MotorCommand command, int speed);
void motorStop();
MotorCommand motorGetCommand();
int motorGetSpeed();
