// extract

#include "stdio.h"
#include "FileHeader.h"
#include "FrameHeader.h"
#include "FrameFuncs.h"
#include <math.h>
#include <string.h>
#include <filesystem>
#include <iostream>
#include <cv.hpp>

#define INVALID_INPUTS      -1
#define CANT_OPEN_INPUT     -2
#define CANT_OPEN_OUTPUT    -3
#define NOT_ARIS_FILE       -4
#define CORRUPT_ARIS_FILE   -5
#define IO_ERROR            -6


int extract(std::ifstream& fpIn, std::ofstream& fpOut, std::string outputPath) {

    ArisFileHeader fileHeader;
    ArisFrameHeader frameHeader;

    fpIn.seekg(0, fpIn.end);
    long fileSize = fpIn.tellg();
    fpIn.seekg(0, fpIn.beg);
    long dataSize = fileSize - sizeof(struct ArisFileHeader);

    // Read file header
    if (!fpIn.read(reinterpret_cast<char*>(&fileHeader), sizeof(struct ArisFileHeader))) {
        std::cerr << "Invalid file header." << std::endl;
        return IO_ERROR;
    }

    // Basic sanity check
    if (fileHeader.Version != ARIS_FILE_SIGNATURE) {
        std::cerr << "Invalid file header." << std::endl;
        return NOT_ARIS_FILE;
    }

    // Read first data frame
    if (!fpIn.read(reinterpret_cast<char*>(&frameHeader), sizeof(struct ArisFrameHeader))) {
        std::cerr << "Couldn't read first frame buffer." << std::endl;
        return CORRUPT_ARIS_FILE;
    }

    // ARIS recordings have a consistent frame size all the way through the file.
    size_t frame_h = frameHeader.SamplesPerBeam;
    size_t frame_w = get_beams_from_pingmode(frameHeader.PingMode);
    long frameSize = frame_h * frame_w;
    long frameCount = dataSize / frameSize;
    
    cv::Mat frame(frame_h, frame_w, CV_8U);

    // CSV header
    fpOut << "FrameIndex;"
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
                "padding"
        << std::endl;


    // Print frame data for each frame.
    do {
        fpOut << frameHeader.FrameIndex;
        fpOut << frameHeader.FrameTime;
        fpOut << frameHeader.Version;
        fpOut << frameHeader.sonarTimeStamp;
        fpOut << frameHeader.TS_Day;
        fpOut << frameHeader.TS_Hour;
        fpOut << frameHeader.TS_Minute;
        fpOut << frameHeader.TS_Second;
        fpOut << frameHeader.TS_Hsecond;
        fpOut << frameHeader.TransmitMode;
        fpOut << isnan(frameHeader.WindowStart)     ? ";" : (double)frameHeader.WindowStart;
        fpOut << isnan(frameHeader.WindowLength)    ? ";" : (double)frameHeader.WindowLength;
        fpOut << frameHeader.Threshold;
        fpOut << frameHeader.Intensity;
        fpOut << frameHeader.ReceiverGain;
        fpOut << frameHeader.DegC1;
        fpOut << frameHeader.DegC2;
        fpOut << frameHeader.Humidity;
        fpOut << frameHeader.Focus;
        fpOut << frameHeader.Battery;
        fpOut << isnan(frameHeader.UserValue1)      ? ";" : (double)frameHeader.UserValue1;
        fpOut << isnan(frameHeader.UserValue2)      ? ";" : (double)frameHeader.UserValue2;
        fpOut << isnan(frameHeader.UserValue3)      ? ";" : (double)frameHeader.UserValue3;
        fpOut << isnan(frameHeader.UserValue4)      ? ";" : (double)frameHeader.UserValue4;
        fpOut << isnan(frameHeader.UserValue5)      ? ";" : (double)frameHeader.UserValue5;
        fpOut << isnan(frameHeader.UserValue6)      ? ";" : (double)frameHeader.UserValue6;
        fpOut << isnan(frameHeader.UserValue7)      ? ";" : (double)frameHeader.UserValue7;
        fpOut << isnan(frameHeader.UserValue8)      ? ";" : (double)frameHeader.UserValue8;
        fpOut << isnan(frameHeader.Velocity)        ? ";" : (double)frameHeader.Velocity;
        fpOut << isnan(frameHeader.Depth)           ? ";" : (double)frameHeader.Depth;
        fpOut << isnan(frameHeader.Altitude)        ? ";" : (double)frameHeader.Altitude;
        fpOut << isnan(frameHeader.Pitch)           ? ";" : (double)frameHeader.Pitch;
        fpOut << isnan(frameHeader.PitchRate)       ? ";" : (double)frameHeader.PitchRate;
        fpOut << isnan(frameHeader.Roll)            ? ";" : (double)frameHeader.Roll;
        fpOut << isnan(frameHeader.RollRate)        ? ";" : (double)frameHeader.RollRate;
        fpOut << isnan(frameHeader.Heading)         ? ";" : (double)frameHeader.Heading;
        fpOut << isnan(frameHeader.HeadingRate)     ? ";" : (double)frameHeader.HeadingRate;
        fpOut << isnan(frameHeader.CompassHeading)  ? ";" : (double)frameHeader.CompassHeading;
        fpOut << isnan(frameHeader.CompassPitch)    ? ";" : (double)frameHeader.CompassPitch;
        fpOut << isnan(frameHeader.CompassRoll)     ? ";" : (double)frameHeader.CompassRoll;
        fpOut << isnan(frameHeader.Latitude)        ? ";" : frameHeader.Latitude;
        fpOut << isnan(frameHeader.Longitude)       ? ";" : frameHeader.Longitude;
        fpOut << isnan(frameHeader.SonarPosition)   ? ";" : (double)frameHeader.SonarPosition;
        fpOut << frameHeader.ConfigFlags;
        fpOut << isnan(frameHeader.BeamTilt)        ? ";" : (double)frameHeader.BeamTilt;
        fpOut << isnan(frameHeader.TargetRange)     ? ";" : (double)frameHeader.TargetRange;
        fpOut << isnan(frameHeader.TargetBearing)   ? ";" : (double)frameHeader.TargetBearing;
        fpOut << frameHeader.TargetPresent;
        fpOut << frameHeader.FirmwareRevision;
        fpOut << frameHeader.Flags;
        fpOut << frameHeader.SourceFrame;
        fpOut << isnan(frameHeader.WaterTemp)       ? ";" : (double)frameHeader.WaterTemp;
        fpOut << frameHeader.TimerPeriod;
        fpOut << isnan(frameHeader.SonarX)          ? ";" : (double)frameHeader.SonarX;
        fpOut << isnan(frameHeader.SonarY)          ? ";" : (double)frameHeader.SonarY;
        fpOut << isnan(frameHeader.SonarZ)          ? ";" : (double)frameHeader.SonarZ;
        fpOut << isnan(frameHeader.SonarPan)        ? ";" : (double)frameHeader.SonarPan;
        fpOut << isnan(frameHeader.SonarTilt)       ? ";" : (double)frameHeader.SonarTilt;
        fpOut << isnan(frameHeader.SonarRoll)       ? ";" : (double)frameHeader.SonarRoll;
        fpOut << isnan(frameHeader.PanPNNL)         ? ";" : (double)frameHeader.PanPNNL;
        fpOut << isnan(frameHeader.TiltPNNL)        ? ";" : (double)frameHeader.TiltPNNL;
        fpOut << isnan(frameHeader.RollPNNL)        ? ";" : (double)frameHeader.RollPNNL;
        fpOut << isnan(frameHeader.VehicleTime)     ? ";" : frameHeader.VehicleTime;
        fpOut << isnan(frameHeader.TimeGGK)         ? ";" : (double)frameHeader.TimeGGK;
        fpOut << frameHeader.DateGGK;
        fpOut << frameHeader.QualityGGK;
        fpOut << frameHeader.NumSatsGGK;
        fpOut << isnan(frameHeader.DOPGGK)          ? ";" : (double)frameHeader.DOPGGK;
        fpOut << isnan(frameHeader.EHTGGK)          ? ";" : (double)frameHeader.EHTGGK;
        fpOut << isnan(frameHeader.HeaveTSS)        ? ";" : (double)frameHeader.HeaveTSS;
        fpOut << frameHeader.YearGPS;
        fpOut << frameHeader.MonthGPS;
        fpOut << frameHeader.DayGPS;
        fpOut << frameHeader.HourGPS;
        fpOut << frameHeader.MinuteGPS;
        fpOut << frameHeader.SecondGPS;
        fpOut << frameHeader.HSecondGPS;
        fpOut << isnan(frameHeader.SonarPanOffset)  ? ";" : (double)frameHeader.SonarPanOffset;
        fpOut << isnan(frameHeader.SonarTiltOffset) ? ";" : (double)frameHeader.SonarTiltOffset;
        fpOut << isnan(frameHeader.SonarRollOffset) ? ";" : (double)frameHeader.SonarRollOffset;
        fpOut << isnan(frameHeader.SonarXOffset)    ? ";" : (double)frameHeader.SonarXOffset;
        fpOut << isnan(frameHeader.SonarYOffset)    ? ";" : (double)frameHeader.SonarYOffset;
        fpOut << isnan(frameHeader.SonarZOffset)    ? ";" : (double)frameHeader.SonarZOffset;

        fpOut << ";\"[";
        for (size_t i = 0; i < 16; i++){
            fpOut << isnan(frameHeader.Tmatrix[i]) ? "nan" : (double)frameHeader.Tmatrix[i];
        }
        fpOut << "]\"";

        fpOut << isnan(frameHeader.SampleRate)      ? ";" : (double)frameHeader.SampleRate;
        fpOut << isnan(frameHeader.AccellX)         ? ";" : (double)frameHeader.AccellX;
        fpOut << isnan(frameHeader.AccellY)         ? ";" : (double)frameHeader.AccellY;
        fpOut << isnan(frameHeader.AccellZ)         ? ";" : (double)frameHeader.AccellZ;
        fpOut << frameHeader.PingMode;
        fpOut << frameHeader.FrequencyHiLow;
        fpOut << frameHeader.PulseWidth;
        fpOut << frameHeader.CyclePeriod;
        fpOut << frameHeader.SamplePeriod;
        fpOut << frameHeader.TransmitEnable;
        fpOut << isnan(frameHeader.FrameRate)       ? ";" : (double)frameHeader.FrameRate;
        fpOut << isnan(frameHeader.SoundSpeed)      ? ";" : (double)frameHeader.SoundSpeed;
        fpOut << frameHeader.SamplesPerBeam;
        fpOut << frameHeader.Enable150V;
        fpOut << frameHeader.SampleStartDelay;
        fpOut << frameHeader.LargeLens;
        fpOut << frameHeader.TheSystemType;
        fpOut << frameHeader.SonarSerialNumber;
        fpOut << frameHeader.ReservedEK;
        fpOut << frameHeader.ArisErrorFlagsUint;
        fpOut << frameHeader.MissedPackets;
        fpOut << frameHeader.ArisAppVersion;
        fpOut << frameHeader.Available2;
        fpOut << frameHeader.ReorderedSamples;
        fpOut << frameHeader.Salinity;
        fpOut << isnan(frameHeader.Pressure)        ? ";" : (double)frameHeader.Pressure;
        fpOut << isnan(frameHeader.BatteryVoltage)  ? ";" : (double)frameHeader.BatteryVoltage;
        fpOut << isnan(frameHeader.MainVoltage)     ? ";" : (double)frameHeader.MainVoltage;
        fpOut << isnan(frameHeader.SwitchVoltage)   ? ";" : (double)frameHeader.SwitchVoltage;
        fpOut << frameHeader.FocusMotorMoving;
        fpOut << frameHeader.VoltageChanging;
        fpOut << frameHeader.FocusTimeoutFault;
        fpOut << frameHeader.FocusOverCurrentFault;
        fpOut << frameHeader.FocusNotFoundFault;
        fpOut << frameHeader.FocusStalledFault;
        fpOut << frameHeader.FPGATimeoutFault;
        fpOut << frameHeader.FPGABusyFault;
        fpOut << frameHeader.FPGAStuckFault;
        fpOut << frameHeader.CPUTempFault;
        fpOut << frameHeader.PSUTempFault;
        fpOut << frameHeader.WaterTempFault;
        fpOut << frameHeader.HumidityFault;
        fpOut << frameHeader.PressureFault;
        fpOut << frameHeader.VoltageReadFault;
        fpOut << frameHeader.VoltageWriteFault;
        fpOut << frameHeader.FocusCurrentPosition;
        fpOut << isnan(frameHeader.TargetPan)       ? ";" : (double)frameHeader.TargetPan;
        fpOut << isnan(frameHeader.TargetTilt)      ? ";" : (double)frameHeader.TargetTilt;
        fpOut << isnan(frameHeader.TargetRoll)      ? ";" : (double)frameHeader.TargetRoll;
        fpOut << frameHeader.PanMotorErrorCode;
        fpOut << frameHeader.TiltMotorErrorCode;
        fpOut << frameHeader.RollMotorErrorCode;
        fpOut << isnan(frameHeader.PanAbsPosition)  ? ";" : (double)frameHeader.PanAbsPosition;
        fpOut << isnan(frameHeader.TiltAbsPosition) ? ";" : (double)frameHeader.TiltAbsPosition;
        fpOut << isnan(frameHeader.RollAbsPosition) ? ";" : (double)frameHeader.RollAbsPosition;
        fpOut << isnan(frameHeader.PanAccelX)       ? ";" : (double)frameHeader.PanAccelX;
        fpOut << isnan(frameHeader.PanAccelY)       ? ";" : (double)frameHeader.PanAccelY;
        fpOut << isnan(frameHeader.PanAccelZ)       ? ";" : (double)frameHeader.PanAccelZ;
        fpOut << isnan(frameHeader.TiltAccelX)      ? ";" : (double)frameHeader.TiltAccelX;
        fpOut << isnan(frameHeader.TiltAccelY)      ? ";" : (double)frameHeader.TiltAccelY;
        fpOut << isnan(frameHeader.TiltAccelZ)      ? ";" : (double)frameHeader.TiltAccelZ;
        fpOut << isnan(frameHeader.RollAccelX)      ? ";" : (double)frameHeader.RollAccelX;
        fpOut << isnan(frameHeader.RollAccelY)      ? ";" : (double)frameHeader.RollAccelY;
        fpOut << isnan(frameHeader.RollAccelZ)      ? ";" : (double)frameHeader.RollAccelZ;
        fpOut << frameHeader.AppliedSettings;
        fpOut << frameHeader.ConstrainedSettings;
        fpOut << frameHeader.InvalidSettings;
        fpOut << frameHeader.EnableInterpacketDelay;
        fpOut << frameHeader.InterpacketDelayPeriod;
        fpOut << frameHeader.Uptime;
        fpOut << frameHeader.ArisAppVersionMajor;
        fpOut << frameHeader.ArisAppVersionMinor;
        fpOut << frameHeader.GoTime;
        fpOut << isnan(frameHeader.PanVelocity)     ? ";" : (double)frameHeader.PanVelocity;
        fpOut << isnan(frameHeader.TiltVelocity)    ? ";" : (double)frameHeader.TiltVelocity;
        fpOut << isnan(frameHeader.RollVelocity)    ? ";" : (double)frameHeader.RollVelocity;
        fpOut << frameHeader.GpsTimeAge;
        fpOut << frameHeader.SystemVariant;
        fpOut << frameHeader.padding;

        fpOut << std::endl;

        // Read the frame and write it to a separate file
        fpIn.read(frame.data, frameSize);
        cv::imwrite(outputPath + "/frame_" + std::to_string(frameHeader.FrameIndex) + ".ppm", cvFrame);

    } while (fread(&frameHeader, sizeof(frameHeader), 1, fpIn) == 1);

    return 0;
}


void show_usage(void) {

    fprintf(stderr, "USAGE:\n");
    fprintf(stderr, "    extract <input-file> <output-folder>\n");
    fprintf(stderr, "\n");
}


int main(int argc, char** argv ) {

    if (argc != 3) {
        fprintf(stderr, "Bad number of arguments.\n");
        return 1;
    }


    std::filesystem::path inputFile = argv[1];
    if (inputFile.empty()) {
        show_usage();
        fprintf(stderr, "No input file provided.\n");
        return CANT_OPEN_INPUT;
    }

    std::filesystem::path outputPath = argv[2];
    if (outputPath.empty()) {
        show_usage();
        fprintf(stderr, "No output path provided.\n");
        return CANT_OPEN_OUTPUT;
    }

    
    std::string filename = inputFile.stem().string();
    std::filesystem::path outputFile = outputPath / inputFile / ".csv";
    
    std::ifstream fpIn(inputFile);
    std::ofstream fpOut(outputFile);

    int result = extract(fpIn, fpOut, outputPath);


    if (result) {
        fprintf(stderr, "An error occurred while extracting data.\n");
    }

    return result;
}
