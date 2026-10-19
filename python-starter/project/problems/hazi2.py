from project.problem import Problem
import argparse
import collections
import sys

class DET(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Initialize the parser with the necessary arguments.
        """
        parser.add_argument(
            '--det',
            help='converts an indefinite automation into a definite one',
            action='store_true'
        )

    def is_chosen_problem(self, args):
        """
        Check if the DFA problem is chosen.
        """
        return bool(args.det)

    def read_automaton(self, input_file):
        """
        Read the NFA from the input file.

        File format:
        1. states
        2. alphabet
        3. start state
        4. final states
        5. transitions: source symbol target
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if len(lines) < 3:
            print("Error: input file has insufficient lines.", file=sys.stderr)
            sys.exit(1)

        states = lines[0].split()
        alphabet = lines[1].split()
        start_state = lines[2]

        state_set = set(states)
        alphabet_set = set(alphabet)

        if start_state not in state_set:
            print(
                f"Error: start state '{start_state}' is not in the first row.",
                file=sys.stderr
            )
            sys.exit(1)

        # Handle final states and transition lines
        if len(lines) > 3:
            tokens_3 = lines[3].split()
            # Check if line 3 is actually a transition (in case final states line was empty)
            if (
                len(tokens_3) == 3
                and tokens_3[0] in state_set
                and tokens_3[1] in alphabet_set
                and tokens_3[2] in state_set
                and tokens_3[1] not in state_set
            ):
                final_states = set()
                transition_lines = lines[3:]
            else:
                final_states = set(tokens_3)
                transition_lines = lines[4:]
        else:
            final_states = set()
            transition_lines = []

        for final_state in final_states:
            if final_state not in state_set:
                print(
                    f"Error: final state '{final_state}' is not in the first row.",
                    file=sys.stderr
                )
                sys.exit(1)

        transitions = {}

        for line in transition_lines:
            parts = line.split()
            if not parts:
                continue

            if len(parts) != 3:
                print(
                    f"Error: transition '{line}' is invalid.",
                    file=sys.stderr
                )
                sys.exit(1)

            source, symbol, target = parts

            if source not in state_set or target not in state_set:
                print(
                    f"Error: transition '{source} {symbol} {target}' contains "
                    "a state that is not in the first row.",
                    file=sys.stderr
                )
                sys.exit(1)

            if symbol not in alphabet_set:
                print(
                    f"Error: transition '{source} {symbol} {target}' contains "
                    "a symbol that is not in the second row.",
                    file=sys.stderr
                )
                sys.exit(1)

            if (source, symbol) not in transitions:
                transitions[(source, symbol)] = set()
            transitions[(source, symbol)].add(target)

        return states, alphabet, start_state, final_states, transitions

    def determinize(self, states, alphabet, start_state, final_states, transitions):
        """
        Determinize the NFA using the subset/powerset construction algorithm.
        """
        # Maintain unique alphabet symbols preserving input order
        unique_alphabet = []
        for sym in alphabet:
            if sym not in unique_alphabet:
                unique_alphabet.append(sym)
        sorted_symbols = sorted(unique_alphabet)

        start_subset = frozenset([start_state])
        dfa_state_map = {start_subset: "s0"}
        dfa_states = ["s0"]
        queue = collections.deque([start_subset])
        dfa_transitions = []

        while queue:
            current_subset = queue.popleft()
            current_name = dfa_state_map[current_subset]

            for symbol in sorted_symbols:
                next_subset = set()
                for q in current_subset:
                    if (q, symbol) in transitions:
                        next_subset.update(transitions[(q, symbol)])

                if not next_subset:
                    continue

                frozen_next = frozenset(next_subset)
                if frozen_next not in dfa_state_map:
                    new_name = f"s{len(dfa_states)}"
                    dfa_state_map[frozen_next] = new_name
                    dfa_states.append(new_name)
                    queue.append(frozen_next)

                target_name = dfa_state_map[frozen_next]
                dfa_transitions.append((current_name, symbol, target_name))

        # Determine DFA final states
        dfa_final_states = [
            name for subset, name in dfa_state_map.items()
            if any(q in final_states for q in subset)
        ]
        dfa_final_states.sort(
            key=lambda s: int(s[1:]) if s.startswith('s') and s[1:].isdigit() else s
        )

        # Sort transitions: source node, edge label, target node
        dfa_transitions.sort(
            key=lambda t: (
                int(t[0][1:]) if t[0].startswith('s') and t[0][1:].isdigit() else t[0],
                t[1],
                int(t[2][1:]) if t[2].startswith('s') and t[2][1:].isdigit() else t[2]
            )
        )

        return dfa_states, unique_alphabet, "s0", dfa_final_states, dfa_transitions

    def run(self, args):
        """
        Run the determinization process.
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

        (
            dfa_states,
            dfa_alphabet,
            dfa_start_state,
            dfa_final_states,
            dfa_transitions
        ) = self.determinize(
            states,
            alphabet,
            start_state,
            final_states,
            transitions
        )

        output_lines = [
            ' '.join(dfa_states),
            ' '.join(dfa_alphabet),
            dfa_start_state,
            ' '.join(dfa_final_states),
        ]

        for src, sym, dst in dfa_transitions:
            output_lines.append(f"{src} {sym} {dst}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines) + '\n')
