from project.problem import Problem
import argparse

class DFA(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Initialize the parser with the necessary arguments.
        """
        parser.add_argument(
            '--dfa',
            help='simulate the deterministic finite automaton',
            action='store_true'
        )
        parser.add_argument(
            '--check',
            help='comma-separated words to check',
            type=str
        )

    def is_chosen_problem(self, args):
        """
        Check if the DFA problem is chosen.
        """
        return bool(args.check)

    def read_automaton(self, input_file):
        """
        Read the DFA from the input file.

        File format:
        1. states
        2. alphabet
        3. start state
        4. final states
        5. transitions: source symbol target
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        states = lines[0].split()
        alphabet = lines[1].split()
        start_state = lines[2]
        final_states = set(lines[3].split())

        transitions = {}

        for line in lines[4:]:
            source, symbol, target = line.split()
            transitions[(source, symbol)] = target

        return states, alphabet, start_state, final_states, transitions

    def accepts(self, word, start_state, final_states, transitions):
        """
        Check whether the DFA accepts the given word.
        """
        current_state = start_state

        for symbol in word:
            if (current_state, symbol) not in transitions:
                return False

            current_state = transitions[(current_state, symbol)]

        return current_state in final_states

    def run(self, args):
        """
        Run the DFA simulation.
        """
        input_file = args.input
        output_file = args.output
        (
            states,
            alphabet,
            start_state,
            final_states,
            transitions
        ) = self.read_automaton(input_file)

        words = args.check.split(',')

        results = []

        for word in words:
            if self.accepts(
                word,
                start_state,
                final_states,
                transitions
            ):
                results.append('IGEN')
            else:
                results.append('NEM')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))
            f.write('\n')