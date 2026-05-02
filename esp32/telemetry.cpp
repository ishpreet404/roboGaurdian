#include "telemetry.h"

static String floatStr(float value, int decimals)
{
    return String(value, decimals);
}

String telemetryToJson(const TelemetryData &data)
{
    String json;
    json.reserve(380);

    json += "{";
    json += "\"pose\":{";
    json += "\"x\":" + floatStr(data.odom.x, 3) + ",";
    json += "\"y\":" + floatStr(data.odom.y, 3) + ",";
    json += "\"heading_deg\":" + floatStr(data.heading_deg, 2);
    json += "},";

    json += "\"imu\":{";
    json += "\"ax\":" + floatStr(data.imu.ax, 3) + ",";
    json += "\"ay\":" + floatStr(data.imu.ay, 3) + ",";
    json += "\"az\":" + floatStr(data.imu.az, 3) + ",";
    json += "\"gx\":" + floatStr(data.imu.gx, 2) + ",";
    json += "\"gy\":" + floatStr(data.imu.gy, 2) + ",";
    json += "\"gz\":" + floatStr(data.imu.gz, 2) + ",";
    json += "\"yaw_deg\":" + floatStr(data.imu.yaw_deg, 2) + ",";
    json += "\"pitch_deg\":" + floatStr(data.imu.pitch_deg, 2) + ",";
    json += "\"roll_deg\":" + floatStr(data.imu.roll_deg, 2);
    json += "},";

    json += "\"gps\":{";
    json += "\"lat\":" + floatStr(data.gps.lat, 6) + ",";
    json += "\"lon\":" + floatStr(data.gps.lon, 6) + ",";
    json += "\"speed_mps\":" + floatStr(data.gps.speed_mps, 2) + ",";
    json += "\"sats\":" + String(data.gps.sats) + ",";
    json += "\"fix\":" + String(data.gps.fix ? "true" : "false");
    json += "},";

    json += "\"odometry\":{";
    json += "\"distance_m\":" + floatStr(data.odom.distance_m, 2) + ",";
    json += "\"speed_mps\":" + floatStr(data.odom.speed_mps, 2);
    json += "},";

    json += "\"sonar_cm\":" + floatStr(data.sonar_cm, 1) + ",";

    json += "\"battery\":{";
    json += "\"voltage\":" + floatStr(data.battery_v, 2) + ",";
    json += "\"percent\":" + floatStr(data.battery_pct, 1);
    json += "},";

    json += "\"motor\":{";
    json += "\"state\":\"" + String(data.motor_state) + "\",";
    json += "\"speed\":" + floatStr(data.motor_speed, 1);
    json += "},";

    json += "\"system\":{";
    json += "\"uptime_sec\":" + floatStr(millis() / 1000.0f, 1) + ",";
    json += "\"mode\":\"auto\"";
    json += "}";

    json += "}";
    return json;
}
