import wpilib
import threading
import vision
import random
import networktables

class Robot(wpilib.IterativeRobot):

    def robotInit(self):
        self.sd = networktables.NetworkTables.getTable('SmartDashboard')
        self.sd.setUpdateRate(0.010)
        self.myRobot=wpilib.RobotDrive(0,1)
        self.myRobot.setExpiration(0.1)

        self.left_stick=wpilib.Joystick(0)
        self.right_stick=wpilib.Joystick(1)

        self.climber=wpilib.Spark(2)

        self.gyro0 = wpilib.AnalogGyro(0)
        self.gyro1 = wpilib.AnalogGyro(1)

        self.cx = 0
        self.last_cx = 0
        self.last_cx_timer = wpilib.Timer()
        self.last_cs_time = self.last_cx_timer.get()
        t = threading.Thread(target = vision.cvThread, args=(self,))
        t.daemon = True
        t.start()
        t = threading.Thread(target = vision.flaskThread)
        t.daemon = True
        t.start()

    #def disabledInit(self):
    #    self.gyro0.calibrate()
    #    self.gyro1.calibrate()

    def autonomousInit(self):
        timer = wpilib.Timer()
        timer.start()
        self.myRobot.setSafetyEnabled(False)

        self.integral = 0.0
        self.last_proportional = None
        self.derivative_timer = wpilib.Timer()
        self.derivative_timer.start()
        self.last_time = self.derivative_timer.get()
        # self.gyro0.reset()
        # self.gyro1.reset()
        # timer = wpilib.Timer()
        # timer.start()
        # i = 0.0
        # P = 0.4
        # I = 0.007
        # D = 0.006
        # while self.isEnabled() and self.isAutonomous():#timer.get() < 6.0:
        #     p = 0.5 * (self.gyro0.getOffset() + self.gyro1.getOffset())
        #     self.sd.putNumber('gyro', p)
        #     i = i * 0.6 + p
        #     d = 0.5 * (self.gyro0.getRate() + self.gyro1.getRate())
        #     turn = P * p + I * i + D * d
        #     print(p, i, d, turn)
        #     self.myRobot.tankDrive(0.6 - turn, 0.6 + turn)
        #
        # self.myRobot.tankDrive(0.0, 0.0)

        lastDone = timer.get()
        self.myRobot.tankDrive(0.6, 0.6)
        wpilib.Timer.delay(0.4)
        self.myRobot.tankDrive(0.0, 0.0)
        while (timer.get() - lastDone < 4.0 or self.cy > 2) and self.isAutonomous() and self.isEnabled():
            self.rotor_drive()
            if self.cy > 2:
                lastDone = timer.get()
        time = timer.get()
        while timer.get() < time + 3.0 and self.isAutonomous() and self.isEnabled():
            self.myRobot.tankDrive(0.47 + random.random() * 0.1, 0.47 + random.random() * 0.1)
        self.myRobot.tankDrive(0.0, 0.0)

    def rotor_drive(self):
        turn = 0.0
        if self.cx is not None:
            proportional = (self.cx - 40.0) / 80.0
            #if self.last_proportional == None:
            #    self.last_proportional = proportional
            #self.integral = self.integral * 0.6 + proportional
            #time = self.derivative_timer.get()
            #dt = time - self.last_time
            #derivative = (proportional - self.last_proportional) / dt
            #if proportional != self.last_proportoinal:
            #    self.last_time = time
            #    self.last_proportional = proportional
            #time = self.last_cx_timer.get()
            turn = proportional * 0.3# + self.integral * 0.0 + derivative * 10
            #print("last prop " + str(self.last_proportional) + "prop " + str(proportional))
            #print("deriv" + str(derivative))
            print(turn)
            #self.last_cx_time = time
            #self.last_cx = d
        if abs(turn) < 0.001:
            turn = 0.0
        if turn > 0.1:
            turn = 0.1
        if turn < -0.1:
            turn = -0.1
        self.myRobot.tankDrive(.5 + turn, .55 - turn)

    def disabledPeriodic (self):
        self.sd.putNumber('gyro', 0.5 * (self.gyro0.getOffset() + self.gyro1.getOffset()))
        wpilib.Timer.delay(0.05)

    def teleopInit(self):
        self.gyro0.reset()
        self.gyro1.reset()
        self.myRobot.setSafetyEnabled(True)

    def teleopPeriodic(self):
        self.sd.putNumber('gyro', 0.5 * (self.gyro0.getOffset() + self.gyro1.getOffset()))

        turn = 0.0
        if self.cx is not None:
            d = (self.cx - 40.0) / 80.0
            turn = d * 0.6
        if abs(turn) < 0.0001:
            turn = 0.0
        if self.left_stick.getRawButton(3):
            value = -self.left_stick.getY()
            self.myRobot.tankDrive(value + turn-.1, value - turn)
        elif self.right_stick.getRawButton(3):
            value = -self.right_stick.getY()
            self.myRobot.tankDrive(value + turn-.1, value - turn)
        else:
            #right and left switched, negative values because wrong direction
            self.myRobot.tankDrive(-self.right_stick.getY(), -self.left_stick.getY())
        wpilib.Timer.delay(0.005)

        if self.left_stick.getTrigger():
            self.climber.set(1.0)
        elif self.right_stick.getTrigger():
            self.climber.set(-1.0)
        else:
            self.climber.set(0)


if __name__ == '__main__':
    wpilib.run(Robot)

#self.destruct.init
