#include "motor.h"

#ifndef MOTOR_IN1_PIN
#define MOTOR_IN1_PIN 27
#endif
#ifndef MOTOR_IN2_PIN
#define MOTOR_IN2_PIN 26
#endif
#ifndef MOTOR_IN3_PIN
#define MOTOR_IN3_PIN 25
#endif
#ifndef MOTOR_IN4_PIN
#define MOTOR_IN4_PIN 33
#endif
#ifndef MOTOR_ENA_PIN
#define MOTOR_ENA_PIN 14
#endif
#ifndef MOTOR_ENB_PIN
#define MOTOR_ENB_PIN 12
#endif

static const int kPwmFreq = 1000;
static const int kPwmResolution = 8;
static const int kPwmChannelA = 0;
static const int kPwmChannelB = 1;

static MotorCommand currentCommand = MOTOR_STOP;
static int currentSpeed = 180;

static void applyPins(MotorCommand command, int speed)
{
    switch (command)
    {
    case MOTOR_FORWARD:
        digitalWrite(MOTOR_IN1_PIN, HIGH);
        digitalWrite(MOTOR_IN2_PIN, LOW);
        digitalWrite(MOTOR_IN3_PIN, HIGH);
        digitalWrite(MOTOR_IN4_PIN, LOW);
        break;
    case MOTOR_BACKWARD:
        digitalWrite(MOTOR_IN1_PIN, LOW);
        digitalWrite(MOTOR_IN2_PIN, HIGH);
        digitalWrite(MOTOR_IN3_PIN, LOW);
        digitalWrite(MOTOR_IN4_PIN, HIGH);
        break;
    case MOTOR_LEFT:
        digitalWrite(MOTOR_IN1_PIN, LOW);
        digitalWrite(MOTOR_IN2_PIN, HIGH);
        digitalWrite(MOTOR_IN3_PIN, HIGH);
        digitalWrite(MOTOR_IN4_PIN, LOW);
        break;
    case MOTOR_RIGHT:
        digitalWrite(MOTOR_IN1_PIN, HIGH);
        digitalWrite(MOTOR_IN2_PIN, LOW);
        digitalWrite(MOTOR_IN3_PIN, LOW);
        digitalWrite(MOTOR_IN4_PIN, HIGH);
        break;
    case MOTOR_STOP:
    default:
        digitalWrite(MOTOR_IN1_PIN, LOW);
        digitalWrite(MOTOR_IN2_PIN, LOW);
        digitalWrite(MOTOR_IN3_PIN, LOW);
        digitalWrite(MOTOR_IN4_PIN, LOW);
        break;
    }

    ledcWrite(kPwmChannelA, speed);
    ledcWrite(kPwmChannelB, speed);
}

void motorInit()
{
    pinMode(MOTOR_IN1_PIN, OUTPUT);
    pinMode(MOTOR_IN2_PIN, OUTPUT);
    pinMode(MOTOR_IN3_PIN, OUTPUT);
    pinMode(MOTOR_IN4_PIN, OUTPUT);
    pinMode(MOTOR_ENA_PIN, OUTPUT);
    pinMode(MOTOR_ENB_PIN, OUTPUT);

    ledcSetup(kPwmChannelA, kPwmFreq, kPwmResolution);
    ledcSetup(kPwmChannelB, kPwmFreq, kPwmResolution);
    ledcAttachPin(MOTOR_ENA_PIN, kPwmChannelA);
    ledcAttachPin(MOTOR_ENB_PIN, kPwmChannelB);

    motorStop();
}

void motorSetCommand(MotorCommand command, int speed)
{
    currentCommand = command;
    currentSpeed = constrain(speed, 0, 255);
    applyPins(command, currentSpeed);
}

void motorStop()
{
    currentCommand = MOTOR_STOP;
    currentSpeed = 0;
    applyPins(MOTOR_STOP, 0);
}

MotorCommand motorGetCommand()
{
    return currentCommand;
}

int motorGetSpeed()
{
    return currentSpeed;
}
