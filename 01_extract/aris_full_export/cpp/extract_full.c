// extract

#include "stdio.h"
#include "FileHeader.h"
#include "FrameHeader.h"
#include "FrameFuncs.h"
#include <math.h>
#include <string.h>
#include <opencv2/opencv.hpp>

#define INVALID_INPUTS      -1
#define CANT_OPEN_INPUT     -2
#define CANT_OPEN_OUTPUT    -3
#define NOT_ARIS_FILE       -4
#define CORRUPT_ARIS_FILE   -5
#define IO_ERROR            -6


int validate_inputs(int argc,
                    char** argv,
                    const char** inputPath,
                    const char** outputPath);
void show_usage(void);
int extract(FILE* fpIn, FILE* fpOut);

int main(int argc, char** argv ) {

    const char* inputPath = NULL;
    const char* outputPath = NULL;
    FILE* fpIn = NULL;
    FILE* fpOut = NULL;

    if (validate_inputs(argc, argv, &inputPath, &outputPath)) {
        show_usage();
        return INVALID_INPUTS;
    }

    fpIn = fopen(inputPath, "rb");
    if (!fpIn) {
        fprintf(stderr, "Couldn't open the input file.\n");
        return CANT_OPEN_INPUT;
    }

    fpOut = fopen(outputPath, "w");
    if (!fpOut) {
        fprintf(stderr, "Couldn't open output file.\n");
        fclose(fpIn);
        return CANT_OPEN_OUTPUT;
    }

    int result = extract(fpIn, fpOut);
    fclose(fpIn);
    fclose(fpOut);

    if (result) {
        fprintf(stderr, "An error occurred while extracting data.\n");
    }

    return result;
}

void show_usage(void) {

    fprintf(stderr, "USAGE:\n");
    fprintf(stderr, "    extract <input-path> <output-path>\n");
    fprintf(stderr, "\n");
}

int validate_inputs(int argc,
                    char** argv,
                    const char** inputPath,
                    const char** outputPath) {

    if (argc != 3) {
        fprintf(stderr, "Bad number of arguments.\n");
        return 1;
    }

    *inputPath = argv[1];
    *outputPath = argv[2];

    if (strlen(*inputPath) == 0) {
        fprintf(stderr, "No input path.\n");
        return 2;
    }

    if (strlen(*outputPath) == 0) {
        fprintf(stderr, "No output path.\n");
        return 3;
    }

    return 0;
}


int extract(FILE* fpIn, FILE* fpOut) {

    struct ArisFileHeader fileHeader;
    struct ArisFrameHeader frameHeader;
    long fileSize = 0, dataSize = 0, frameSize = 0, frameCount = 0;

    if (fseek(fpIn, 0, SEEK_END)) {
        fprintf(stderr, "Couldn't determine file size.\n");
        return IO_ERROR;
    }

    fileSize = ftell(fpIn);
    fseek(fpIn, 0, SEEK_SET);
    dataSize = fileSize - sizeof(struct ArisFileHeader);

    if (fread(&fileHeader, sizeof(fileHeader), 1, fpIn) != 1) {
        fprintf(stderr, "Couldn't read complete file header.\n");
        return NOT_ARIS_FILE;
    }

    if (fileHeader.Version != ARIS_FILE_SIGNATURE) {
        fprintf(stderr, "Invalid file header.\n");
        return NOT_ARIS_FILE;
    }

    if (fread(&frameHeader, sizeof(frameHeader), 1, fpIn) != 1) {
        fprintf(stderr, "Couldn't read first frame buffer.\n");
        return CORRUPT_ARIS_FILE;
    }

    // ARIS recordings have a consistent frame size all the way through the file.
    frameSize = (long)(frameHeader.SamplesPerBeam * get_beams_from_pingmode(frameHeader.PingMode));
    frameCount = dataSize / frameSize;
    (void)frameCount; // not actually using this variable
    
    uint8_t frame[frameSize];

    // CSV header
    fprintf(fpOut,  "FrameIndex;"
                    "FrameTime;"
                    "Version;"
                    "sonarTimeStamp;"
                    "TS_Day;"
                    "TS_Hour;"
                    "TS_Minute;"
                    "TS_Second;"
                    "TS_Hsecond;"
                    "TransmitMode;"
                    "WindowStart;"
                    "WindowLength;"
                    "Threshold;"
                    "Intensity;"
                    "ReceiverGain;"
                    "DegC1;"
                    "DegC2;"
                    "Humidity;"
                    "Focus;"
                    "Battery;"
                    "UserValue1;"
                    "UserValue2;"
                    "UserValue3;"
                    "UserValue4;"
                    "UserValue5;"
                    "UserValue6;"
                    "UserValue7;"
                    "UserValue8;"
                    "Velocity;"
                    "Depth;"
                    "Altitude;"
                    "Pitch;"
                    "PitchRate;"
                    "Roll;"
                    "RollRate;"
                    "Heading;"
                    "HeadingRate;"
                    "CompassHeading;"
                    "CompassPitch;"
                    "CompassRoll;"
                    "Latitude;"
                    "Longitude;"
                    "SonarPosition;"
                    "ConfigFlags;"
                    "BeamTilt;"
                    "TargetRange;"
                    "TargetBearing;"
                    "TargetPresent;"
                    "FirmwareRevision;"
                    "Flags;"
                    "SourceFrame;"
                    "WaterTemp;"
                    "TimerPeriod;"
                    "SonarX;"
                    "SonarY;"
                    "SonarZ;"
                    "SonarPan;"
                    "SonarTilt;"
                    "SonarRoll;"
                    "PanPNNL;"
                    "TiltPNNL;"
                    "RollPNNL;"
                    "VehicleTime;"
                    "TimeGGK;"
                    "DateGGK;"
                    "QualityGGK;"
                    "NumSatsGGK;"
                    "DOPGGK;"
                    "EHTGGK;"
                    "HeaveTSS;"
                    "YearGPS;"
                    "MonthGPS;"
                    "DayGPS;"
                    "HourGPS;"
                    "MinuteGPS;"
                    "SecondGPS;"
                    "HSecondGPS;"
                    "SonarPanOffset;"
                    "SonarTiltOffset;"
                    "SonarRollOffset;"
                    "SonarXOffset;"
                    "SonarYOffset;"
                    "SonarZOffset;"
                    "Tmatrix;"
                    "SampleRate;"
                    "AccellX;"
                    "AccellY;"
                    "AccellZ;"
                    "PingMode;"
                    "FrequencyHiLow;"
                    "PulseWidth;"
                    "CyclePeriod;"
                    "SamplePeriod;"
                    "TransmitEnable;"
                    "FrameRate;"
                    "SoundSpeed;"
                    "SamplesPerBeam;"
                    "Enable150V;"
                    "SampleStartDelay;"
                    "LargeLens;"
                    "TheSystemType;"
                    "SonarSerialNumber;"
                    "ReservedEK;"
                    "ArisErrorFlagsUint;"
                    "MissedPackets;"
                    "ArisAppVersion;"
                    "Available2;"
                    "ReorderedSamples;"
                    "Salinity;"
                    "Pressure;"
                    "BatteryVoltage;"
                    "MainVoltage;"
                    "SwitchVoltage;"
                    "FocusMotorMoving;"
                    "VoltageChanging;"
                    "FocusTimeoutFault;"
                    "FocusOverCurrentFault;"
                    "FocusNotFoundFault;"
                    "FocusStalledFault;"
                    "FPGATimeoutFault;"
                    "FPGABusyFault;"
                    "FPGAStuckFault;"
                    "CPUTempFault;"
                    "PSUTempFault;"
                    "WaterTempFault;"
                    "HumidityFault;"
                    "PressureFault;"
                    "VoltageReadFault;"
                    "VoltageWriteFault;"
                    "FocusCurrentPosition;"
                    "TargetPan;"
                    "TargetTilt;"
                    "TargetRoll;"
                    "PanMotorErrorCode;"
                    "TiltMotorErrorCode;"
                    "RollMotorErrorCode;"
                    "PanAbsPosition;"
                    "TiltAbsPosition;"
                    "RollAbsPosition;"
                    "PanAccelX;"
                    "PanAccelY;"
                    "PanAccelZ;"
                    "TiltAccelX;"
                    "TiltAccelY;"
                    "TiltAccelZ;"
                    "RollAccelX;"
                    "RollAccelY;"
                    "RollAccelZ;"
                    "AppliedSettings;"
                    "ConstrainedSettings;"
                    "InvalidSettings;"
                    "EnableInterpacketDelay;"
                    "InterpacketDelayPeriod;"
                    "Uptime;"
                    "ArisAppVersionMajor;"
                    "ArisAppVersionMinor;"
                    "GoTime;"
                    "PanVelocity;"
                    "TiltVelocity;"
                    "RollVelocity;"
                    "GpsTimeAge;"
                    "SystemVariant;"
                    "padding\n");


    // Print frame data for each frame.
    do {
        fprintf(fpOut, "%u", frameHeader.FrameIndex);
        fprintf(fpOut, ";%lu", frameHeader.FrameTime);
        fprintf(fpOut, ";%u", frameHeader.Version);
        fprintf(fpOut, ";%lu", frameHeader.sonarTimeStamp);
        fprintf(fpOut, ";%u", frameHeader.TS_Day);
        fprintf(fpOut, ";%u", frameHeader.TS_Hour);
        fprintf(fpOut, ";%u", frameHeader.TS_Minute);
        fprintf(fpOut, ";%u", frameHeader.TS_Second);
        fprintf(fpOut, ";%u", frameHeader.TS_Hsecond);
        fprintf(fpOut, ";%u", frameHeader.TransmitMode);
        isnan(frameHeader.WindowStart)     ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.WindowStart);
        isnan(frameHeader.WindowLength)    ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.WindowLength);
        fprintf(fpOut, ";%u", frameHeader.Threshold);
        fprintf(fpOut, ";%i", frameHeader.Intensity);
        fprintf(fpOut, ";%u", frameHeader.ReceiverGain);
        fprintf(fpOut, ";%u", frameHeader.DegC1);
        fprintf(fpOut, ";%u", frameHeader.DegC2);
        fprintf(fpOut, ";%u", frameHeader.Humidity);
        fprintf(fpOut, ";%u", frameHeader.Focus);
        fprintf(fpOut, ";%u", frameHeader.Battery);
        isnan(frameHeader.UserValue1)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.UserValue1);
        isnan(frameHeader.UserValue2)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.UserValue2);
        isnan(frameHeader.UserValue3)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.UserValue3);
        isnan(frameHeader.UserValue4)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.UserValue4);
        isnan(frameHeader.UserValue5)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.UserValue5);
        isnan(frameHeader.UserValue6)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.UserValue6);
        isnan(frameHeader.UserValue7)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.UserValue7);
        isnan(frameHeader.UserValue8)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.UserValue8);
        isnan(frameHeader.Velocity)        ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.Velocity);
        isnan(frameHeader.Depth)           ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.Depth);
        isnan(frameHeader.Altitude)        ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.Altitude);
        isnan(frameHeader.Pitch)           ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.Pitch);
        isnan(frameHeader.PitchRate)       ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.PitchRate);
        isnan(frameHeader.Roll)            ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.Roll);
        isnan(frameHeader.RollRate)        ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.RollRate);
        isnan(frameHeader.Heading)         ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.Heading);
        isnan(frameHeader.HeadingRate)     ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.HeadingRate);
        isnan(frameHeader.CompassHeading)  ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.CompassHeading);
        isnan(frameHeader.CompassPitch)    ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.CompassPitch);
        isnan(frameHeader.CompassRoll)     ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.CompassRoll);
        isnan(frameHeader.Latitude)        ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", frameHeader.Latitude);
        isnan(frameHeader.Longitude)       ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", frameHeader.Longitude);
        isnan(frameHeader.SonarPosition)   ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarPosition);
        fprintf(fpOut, ";%u", frameHeader.ConfigFlags);
        isnan(frameHeader.BeamTilt)        ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.BeamTilt);
        isnan(frameHeader.TargetRange)     ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TargetRange);
        isnan(frameHeader.TargetBearing)   ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TargetBearing);
        fprintf(fpOut, ";%u", frameHeader.TargetPresent);
        fprintf(fpOut, ";%u", frameHeader.FirmwareRevision);
        fprintf(fpOut, ";%u", frameHeader.Flags);
        fprintf(fpOut, ";%u", frameHeader.SourceFrame);
        isnan(frameHeader.WaterTemp)       ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.WaterTemp);
        fprintf(fpOut, ";%u", frameHeader.TimerPeriod);
        isnan(frameHeader.SonarX)          ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarX);
        isnan(frameHeader.SonarY)          ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarY);
        isnan(frameHeader.SonarZ)          ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarZ);
        isnan(frameHeader.SonarPan)        ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarPan);
        isnan(frameHeader.SonarTilt)       ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarTilt);
        isnan(frameHeader.SonarRoll)       ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarRoll);
        isnan(frameHeader.PanPNNL)         ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.PanPNNL);
        isnan(frameHeader.TiltPNNL)        ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TiltPNNL);
        isnan(frameHeader.RollPNNL)        ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.RollPNNL);
        isnan(frameHeader.VehicleTime)     ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", frameHeader.VehicleTime);
        isnan(frameHeader.TimeGGK)         ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TimeGGK);
        fprintf(fpOut, ";%u", frameHeader.DateGGK);
        fprintf(fpOut, ";%u", frameHeader.QualityGGK);
        fprintf(fpOut, ";%u", frameHeader.NumSatsGGK);
        isnan(frameHeader.DOPGGK)          ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.DOPGGK);
        isnan(frameHeader.EHTGGK)          ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.EHTGGK);
        isnan(frameHeader.HeaveTSS)        ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.HeaveTSS);
        fprintf(fpOut, ";%u", frameHeader.YearGPS);
        fprintf(fpOut, ";%u", frameHeader.MonthGPS);
        fprintf(fpOut, ";%u", frameHeader.DayGPS);
        fprintf(fpOut, ";%u", frameHeader.HourGPS);
        fprintf(fpOut, ";%u", frameHeader.MinuteGPS);
        fprintf(fpOut, ";%u", frameHeader.SecondGPS);
        fprintf(fpOut, ";%u", frameHeader.HSecondGPS);
        isnan(frameHeader.SonarPanOffset)  ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarPanOffset);
        isnan(frameHeader.SonarTiltOffset) ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarTiltOffset);
        isnan(frameHeader.SonarRollOffset) ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarRollOffset);
        isnan(frameHeader.SonarXOffset)    ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarXOffset);
        isnan(frameHeader.SonarYOffset)    ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarYOffset);
        isnan(frameHeader.SonarZOffset)    ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SonarZOffset);

        fprintf(fpOut, ";\"[");
        for (size_t i = 0; i < 16; i++){
            isnan(frameHeader.Tmatrix[i])  ? fprintf(fpOut, "nan,") : fprintf(fpOut, "%f,", (double)frameHeader.Tmatrix[i]);
        }
        fprintf(fpOut, "]\"");

        isnan(frameHeader.SampleRate)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SampleRate);
        isnan(frameHeader.AccellX)         ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.AccellX);
        isnan(frameHeader.AccellY)         ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.AccellY);
        isnan(frameHeader.AccellZ)         ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.AccellZ);
        fprintf(fpOut, ";%u", frameHeader.PingMode);
        fprintf(fpOut, ";%u", frameHeader.FrequencyHiLow);
        fprintf(fpOut, ";%u", frameHeader.PulseWidth);
        fprintf(fpOut, ";%u", frameHeader.CyclePeriod);
        fprintf(fpOut, ";%u", frameHeader.SamplePeriod);
        fprintf(fpOut, ";%u", frameHeader.TransmitEnable);
        isnan(frameHeader.FrameRate)       ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.FrameRate);
        isnan(frameHeader.SoundSpeed)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SoundSpeed);
        fprintf(fpOut, ";%u", frameHeader.SamplesPerBeam);
        fprintf(fpOut, ";%u", frameHeader.Enable150V);
        fprintf(fpOut, ";%u", frameHeader.SampleStartDelay);
        fprintf(fpOut, ";%u", frameHeader.LargeLens);
        fprintf(fpOut, ";%u", frameHeader.TheSystemType);
        fprintf(fpOut, ";%u", frameHeader.SonarSerialNumber);
        fprintf(fpOut, ";%lu", frameHeader.ReservedEK);
        fprintf(fpOut, ";%u", frameHeader.ArisErrorFlagsUint);
        fprintf(fpOut, ";%u", frameHeader.MissedPackets);
        fprintf(fpOut, ";%u", frameHeader.ArisAppVersion);
        fprintf(fpOut, ";%u", frameHeader.Available2);
        fprintf(fpOut, ";%u", frameHeader.ReorderedSamples);
        fprintf(fpOut, ";%u", frameHeader.Salinity);
        isnan(frameHeader.Pressure)        ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.Pressure);
        isnan(frameHeader.BatteryVoltage)  ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.BatteryVoltage);
        isnan(frameHeader.MainVoltage)     ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.MainVoltage);
        isnan(frameHeader.SwitchVoltage)   ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.SwitchVoltage);
        fprintf(fpOut, ";%u", frameHeader.FocusMotorMoving);
        fprintf(fpOut, ";%u", frameHeader.VoltageChanging);
        fprintf(fpOut, ";%u", frameHeader.FocusTimeoutFault);
        fprintf(fpOut, ";%u", frameHeader.FocusOverCurrentFault);
        fprintf(fpOut, ";%u", frameHeader.FocusNotFoundFault);
        fprintf(fpOut, ";%u", frameHeader.FocusStalledFault);
        fprintf(fpOut, ";%u", frameHeader.FPGATimeoutFault);
        fprintf(fpOut, ";%u", frameHeader.FPGABusyFault);
        fprintf(fpOut, ";%u", frameHeader.FPGAStuckFault);
        fprintf(fpOut, ";%u", frameHeader.CPUTempFault);
        fprintf(fpOut, ";%u", frameHeader.PSUTempFault);
        fprintf(fpOut, ";%u", frameHeader.WaterTempFault);
        fprintf(fpOut, ";%u", frameHeader.HumidityFault);
        fprintf(fpOut, ";%u", frameHeader.PressureFault);
        fprintf(fpOut, ";%u", frameHeader.VoltageReadFault);
        fprintf(fpOut, ";%u", frameHeader.VoltageWriteFault);
        fprintf(fpOut, ";%u", frameHeader.FocusCurrentPosition);
        isnan(frameHeader.TargetPan)       ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TargetPan);
        isnan(frameHeader.TargetTilt)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TargetTilt);
        isnan(frameHeader.TargetRoll)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TargetRoll);
        fprintf(fpOut, ";%u", frameHeader.PanMotorErrorCode);
        fprintf(fpOut, ";%u", frameHeader.TiltMotorErrorCode);
        fprintf(fpOut, ";%u", frameHeader.RollMotorErrorCode);
        isnan(frameHeader.PanAbsPosition)  ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.PanAbsPosition);
        isnan(frameHeader.TiltAbsPosition) ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TiltAbsPosition);
        isnan(frameHeader.RollAbsPosition) ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.RollAbsPosition);
        isnan(frameHeader.PanAccelX)       ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.PanAccelX);
        isnan(frameHeader.PanAccelY)       ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.PanAccelY);
        isnan(frameHeader.PanAccelZ)       ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.PanAccelZ);
        isnan(frameHeader.TiltAccelX)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TiltAccelX);
        isnan(frameHeader.TiltAccelY)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TiltAccelY);
        isnan(frameHeader.TiltAccelZ)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TiltAccelZ);
        isnan(frameHeader.RollAccelX)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.RollAccelX);
        isnan(frameHeader.RollAccelY)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.RollAccelY);
        isnan(frameHeader.RollAccelZ)      ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.RollAccelZ);
        fprintf(fpOut, ";%u", frameHeader.AppliedSettings);
        fprintf(fpOut, ";%u", frameHeader.ConstrainedSettings);
        fprintf(fpOut, ";%u", frameHeader.InvalidSettings);
        fprintf(fpOut, ";%u", frameHeader.EnableInterpacketDelay);
        fprintf(fpOut, ";%u", frameHeader.InterpacketDelayPeriod);
        fprintf(fpOut, ";%u", frameHeader.Uptime);
        fprintf(fpOut, ";%i", (int)frameHeader.ArisAppVersionMajor);
        fprintf(fpOut, ";%i", (int)frameHeader.ArisAppVersionMinor);
        fprintf(fpOut, ";%lu", frameHeader.GoTime);
        isnan(frameHeader.PanVelocity)     ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.PanVelocity);
        isnan(frameHeader.TiltVelocity)    ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.TiltVelocity);
        isnan(frameHeader.RollVelocity)    ? fprintf(fpOut, ";") : fprintf(fpOut, ";%f", (double)frameHeader.RollVelocity);
        fprintf(fpOut, ";%u", frameHeader.GpsTimeAge);
        fprintf(fpOut, ";%u", frameHeader.SystemVariant);
        fprintf(fpOut, ";%s", frameHeader.padding);

        fprintf(fpOut, "\n");

        // Read the frame and write it to a separate file
        // size_t frame_w = get_beams_from_pingmode(frameHeader.PingMode);
        // size_t frame_h = frameHeader.SamplesPerBeam;
        // fread(frame, sizeof(uint8_t), frameSize, fpIn);
        // cv::Mat cvFrame = cv::Mat(frame_h, frame_w, CV_8U, frame);
        // cv::imwrite("frame_" + itos(frameHeader.FrameIndex) + ".ppm", cvFrame);

    } while (fread(&frameHeader, sizeof(frameHeader), 1, fpIn) == 1);

    return 0;
}
