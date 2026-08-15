from manim import *
import numpy as np


class MatrixTransform3D(ThreeDScene):
    def construct(self):

        # Your old 2D matrix:
        #
        # [ 3   3 ]
        # [-2   4 ]
        #
        # Extended into 3D.
        # z is unchanged.
        A = np.array([
            [ 3,  3, 0],
            [-2,  4, 0],
            [ 0,  0, 1]
        ], dtype=float)

        A_inv = np.linalg.inv(A)

        # Camera
        self.set_camera_orientation(
            phi=70 * DEGREES,
            theta=-45 * DEGREES
        )

        # Fixed coordinate axes
        axes = ThreeDAxes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            z_range=[-5, 5, 1],
            x_length=10,
            y_length=10,
            z_length=10,
        )

        self.add(axes)

        # --------------------------------
        # Input basis vectors
        # --------------------------------

        e1 = Arrow3D(
            start=ORIGIN,
            end=[1, 0, 0],
            color=RED
        )

        e2 = Arrow3D(
            start=ORIGIN,
            end=[0, 1, 0],
            color=GREEN
        )

        e3 = Arrow3D(
            start=ORIGIN,
            end=[0, 0, 1],
            color=BLUE
        )

        # Cube lets you SEE the space deform
        cube = Cube(
            side_length=2,
            fill_opacity=0.08,
            stroke_width=1
        )

        moving_objects = Group(
            cube,
            e1,
            e2,
            e3
        )

        self.add(moving_objects)

        self.wait(1)

        # Keep a ghost of original space
        ghost = moving_objects.copy()
        ghost.set_opacity(0.15)
        self.add(ghost)

        # --------------------------------
        # Forward transformation A
        # --------------------------------

        transformed = moving_objects.copy()
        transformed.apply_matrix(A)

        self.play(
            Transform(moving_objects, transformed),
            run_time=3
        )

        self.wait(2)

        # --------------------------------
        # Apply A^-1
        # --------------------------------

        inverse_target = moving_objects.copy()
        inverse_target.apply_matrix(A_inv)

        self.play(
            Transform(moving_objects, inverse_target),
            run_time=3
        )

        self.wait(2)