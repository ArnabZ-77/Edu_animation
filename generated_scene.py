from manim import *

class ExpandBlueCircle(Scene):
    def construct(self):
        # Create a blue circle
        circle = Circle(radius=1, color=BLUE, fill_opacity=1)

        # Add the circle to the scene, growing from its center
        self.play(GrowFromCenter(circle))
        self.wait(0.5)

        # Animate the circle expanding to twice its current size
        self.play(circle.animate.scale(2))
        self.wait(1)

        # Optionally, fade it out
        self.play(FadeOut(circle))
        self.wait(0.5)