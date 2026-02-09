# pylint: disable=no-member
"""
This module defines the MotorController class for controlling the robot's motors.
"""
from RPi import GPIO


class MotorController:
    """A class to control the motors of the robot."""

    def __init__(self, pins=None):
        """
        Initializes the MotorController.

        Args:
            pins (dict, optional): A dictionary of motor pins.
                                   Defaults to None.
        """
        if pins is None:
            self.pins = {
                'in1': 5, 'in2': 6, 'in3': 17, 'in4': 26,
                'ena': 20, 'enb': 21
            }
        else:
            self.pins = pins

        for pin in self.pins.values():
            GPIO.setup(pin, GPIO.OUT)

        self.p1 = GPIO.PWM(self.pins['ena'], 1000)
        self.p2 = GPIO.PWM(self.pins['enb'], 1000)
        self.p1.start(75)
        self.p2.start(75)

    def forward(self):
        """Moves the robot forward."""
        GPIO.output(self.pins['in1'], GPIO.HIGH)
        GPIO.output(self.pins['in2'], GPIO.LOW)
        GPIO.output(self.pins['in3'], GPIO.HIGH)
        GPIO.output(self.pins['in4'], GPIO.LOW)

    def backward(self):
        """Moves the robot backward."""
        GPIO.output(self.pins['in1'], GPIO.LOW)
        GPIO.output(self.pins['in2'], GPIO.HIGH)
        GPIO.output(self.pins['in3'], GPIO.LOW)
        GPIO.output(self.pins['in4'], GPIO.HIGH)

    def left(self):
        """Turns the robot left."""
        GPIO.output(self.pins['in1'], GPIO.LOW)
        GPIO.output(self.pins['in2'], GPIO.HIGH)
        GPIO.output(self.pins['in3'], GPIO.HIGH)
        GPIO.output(self.pins['in4'], GPIO.LOW)

    def right(self):
        """Turns the robot right."""
        GPIO.output(self.pins['in1'], GPIO.HIGH)
        GPIO.output(self.pins['in2'], GPIO.LOW)
        GPIO.output(self.pins['in3'], GPIO.LOW)
        GPIO.output(self.pins['in4'], GPIO.HIGH)

    def stop(self):
        """Stops the robot."""
        GPIO.output(self.pins['in1'], GPIO.LOW)
        GPIO.output(self.pins['in2'], GPIO.LOW)
        GPIO.output(self.pins['in3'], GPIO.LOW)
        GPIO.output(self.pins['in4'], GPIO.LOW)

    def set_speed(self, speed):
        """
        Sets the speed of the motors.

        Args:
            speed (int): The speed of the motors (0-100).
        """
        self.p1.ChangeDutyCycle(speed)
        self.p2.ChangeDutyCycle(speed)
