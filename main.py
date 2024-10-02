"""
@title : Google Hash Code 2016
@description : Main file of the Google Hash Code 2016 Challenge
"""

from parser import parse_challenge
from solver import solve, score_solution, save_solution
from copy import deepcopy

if __name__ == "__main__":

    # Fetching the argument of the runned command (taking the files to solve as an input)
    import argparse
    parser = argparse.ArgumentParser(description='Solve Google Hash challenge.')
    parser.add_argument('challenge', type=str,
                        help='challenge definition filename',
                        metavar="challenge.txt")
    parser.add_argument('output', type=str, default=None,
                        help='output filename',
                        metavar="output.txt")
    args = parser.parse_args()

    # Parsing a given file into a Challenge object
    challenge = parse_challenge(args.challenge)

    saved_challenge = deepcopy(challenge)
    
    # Calculating an optimized solution for the given file
    solution = solve(challenge)

    if args.output is not None:
        # Saving the solution in a file
        save_solution(args.output, solution)
        print(f"Solution saved in {args.output}")
    print(f"Score: {score_solution(solution, saved_challenge)}")
