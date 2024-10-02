"""
@title : Segment
@description : Class defining what is a segment
"""

from utils.types import Action, Location
from utils.Challenge import Challenge


class Segment:
    """
        A segment is a group of actions that can be attributed on its own to a drone, so it doesn't have to calculate
        and mesure all the possibilities among the actions.

        Class is defined by:
            - start
            - end
            - challenge
            - actions
            - order_id
        """

    """ Constructor """

    def __init__(self, start: Location, end: Location, challenge: Challenge, actions: list[Action], order_id: id):
        self.order_id = order_id
        self.start = start
        self.end = end
        self.actions = actions
        self.turns = self.calcul_turns(challenge)

    def calcul_turns(self, challenge: Challenge):
        """
            - Calculate the turns of a challenge
            :return:        The turns
        """
        turns = 0

        pos = self.start

        for action in self.actions:
            # Fetch the location of the action
            location = challenge.get_location(action)
            # Add turns for movement (after deliver / load)
            turns += Challenge.calculate_distance(pos, location) + 1
            # Update the location of the drone
            pos = location

        return turns
