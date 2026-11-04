import argparse
import re
import sys
try:
    from project.problem import Problem
except ImportError:
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from project.problem import Problem


class MINI(Problem):
    """
    Minimizes a deterministic finite automaton (DFA) using table-filling.
    """

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--mini',
            help='minimize the deterministic finite automaton',
            action='store_true'
        )

    def is_chosen_problem(self, args):
        return bool(args.mini)

    def state_sort_key(self, state_name):
        # Custom sort key to sort states naturally (e.g. q0 < q1 < q2 < ... < q10)
        match = re.match(r'^([a-zA-Z]+)(\d+)$', state_name)
        if match:
            prefix, num = match.groups()
            return (0, prefix, int(num))
        # Fallback for states without trailing digits
        return (1, state_name, 0)

    def convert_to_s_name(self, name):
        # If the state name begins with 'q', replace with 's' (e.g. q1 -> s1)
        if name.startswith('q'):
            return 's' + name[1:]
        # If the state name already starts with 's', retain it
        if name.startswith('s'):
            return name
        # For other state names, prepend 's'
        return 's' + name

    def read_automaton(self, input_file):
        # Read all non-empty lines from the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        # Ensure the file contains at least the states, alphabet, and start state
        if len(lines) < 3:
            print("Error: input file has insufficient lines.", file=sys.stderr)
            sys.exit(1)

        # Parse the states from the first line
        states = lines[0].split()
        # Parse the alphabet symbols from the second line
        alphabet = lines[1].split()
        # Parse the start state from the third line
        start_state = lines[2]

        # Use sets for fast membership validation
        state_set = set(states)
        alphabet_set = set(alphabet)

        # Validate that the start state is among the defined states
        if start_state not in state_set:
            print(f"Error: start state '{start_state}' is not in the first row.", file=sys.stderr)
            sys.exit(1)

        # Identify final states line and transition lines
        if len(lines) > 3:
            tokens_3 = lines[3].split()
            # Check if line 3 is actually a transition (when final states line is omitted or empty)
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

        # Validate that all final states are defined in the states list
        for final_state in final_states:
            if final_state not in state_set:
                print(f"Error: final state '{final_state}' is not in the first row.", file=sys.stderr)
                sys.exit(1)

        # Read and validate all transitions
        transitions = {}
        for line in transition_lines:
            parts = line.split()
            if not parts:
                continue

            # Ensure the transition line contains source, symbol, target
            if len(parts) != 3:
                print(f"Error: transition '{line}' is invalid.", file=sys.stderr)
                sys.exit(1)

            source, symbol, target = parts

            # Validate that the source state exists in the state set
            if source not in state_set:
                print(f"Error: transition '{line}' contains unknown source state '{source}'.", file=sys.stderr)
                sys.exit(1)

            # Validate that the target state exists in the state set
            if target not in state_set:
                print(f"Error: transition '{line}' contains unknown target state '{target}'.", file=sys.stderr)
                sys.exit(1)

            # Validate that the symbol exists in the alphabet
            if symbol not in alphabet_set:
                print(f"Error: transition '{line}' contains unknown symbol '{symbol}'.", file=sys.stderr)
                sys.exit(1)

            # Make sure the input automaton is deterministic (at most one transition per (state, symbol))
            if (source, symbol) in transitions:
                if transitions[(source, symbol)] != target:
                    print(f"Error: automaton is not deterministic for transition from '{source}' on '{symbol}'.", file=sys.stderr)
                    sys.exit(1)
            else:
                transitions[(source, symbol)] = target

        # Make sure the input automaton is complete (transition defined for every state and symbol)
        for state in states:
            for symbol in alphabet:
                if (state, symbol) not in transitions:
                    print(f"Error: automaton is not complete. Missing transition for state '{state}' on symbol '{symbol}'.", file=sys.stderr)
                    sys.exit(1)

        return states, alphabet, start_state, final_states, transitions

    def minimize(self, states, alphabet, start_state, final_states, transitions):
        # Step 1: Write down the transition table
        # Map each state and symbol to the corresponding target state
        transition_table = {
            state: {sym: transitions[(state, sym)] for sym in alphabet}
            for state in states
        }

        # Step 2: List all possible pairs of states
        # Compare every state with every other state (all unordered pairs)
        pairs = []
        for i in range(len(states)):
            for j in range(i + 1, len(states)):
                pairs.append((states[i], states[j]))

        # Helper dictionary to track marked (distinguishable) state pairs
        marked_table = {}

        # Step 3: Mark pairs that are immediately distinguishable
        # A pair is distinguishable if exactly one state is accepting and the other is non-accepting
        for p, q in pairs:
            is_p_final = p in final_states
            is_q_final = q in final_states
            # Mark the pair if acceptance status differs
            if is_p_final != is_q_final:
                marked_table[(p, q)] = True
            else:
                marked_table[(p, q)] = False

        # Helper function to check if a pair of states is marked
        def is_marked(u, v):
            # Identical states can never be distinguished
            if u == v:
                return False
            # Look up pair in either order in marked_table
            if (u, v) in marked_table:
                return marked_table[(u, v)]
            return marked_table.get((v, u), False)

        # Step 4 & Step 5: Check transitions for every remaining pair and repeat
        # Multiple passes are performed until no additional pairs can be marked
        changed = True
        while changed:
            # Reset flag at the beginning of each iteration pass
            changed = False
            # Check every pair that is not yet marked
            for p, q in pairs:
                if marked_table[(p, q)]:
                    continue
                # Examine transitions for each symbol in the alphabet
                for sym in alphabet:
                    next_p = transition_table[p][sym]
                    next_q = transition_table[q][sym]
                    # If target states lead to an already marked pair, mark (p, q)
                    if is_marked(next_p, next_q):
                        marked_table[(p, q)] = True
                        changed = True
                        break

        # Step 6: Stop when no more pairs can be marked

        # Step 7: Merge equivalent states
        # Unmarked pairs correspond to equivalent states that should be merged
        parent = {state: state for state in states}

        # Disjoint set union find with path compression
        def find(s):
            if parent[s] != s:
                parent[s] = find(parent[s])
            return parent[s]

        # Union operation to combine two equivalence classes
        def union(s1, s2):
            root1 = find(s1)
            root2 = find(s2)
            if root1 != root2:
                parent[root2] = root1

        # Merge sets for all remaining unmarked pairs
        for p, q in pairs:
            if not marked_table[(p, q)]:
                union(p, q)

        # Group original states by their connected component root
        components = {}
        for state in states:
            root = find(state)
            if root not in components:
                components[root] = []
            components[root].append(state)

        # Assign new names to merged equivalence classes
        state_to_new_name = {}
        new_states_set = set()

        for root, group in components.items():
            # Pick the state with the smallest name as the representative
            rep = min(group, key=self.state_sort_key)
            # Create new name using 's' prefix based on the representative state
            new_name = self.convert_to_s_name(rep)
            # Map each state in this equivalence class to the new name
            for member in group:
                state_to_new_name[member] = new_name
            new_states_set.add(new_name)

        # Sort the minimized states using natural sort order
        sorted_new_states = sorted(list(new_states_set), key=self.state_sort_key)

        # Determine the start state of the minimized automaton
        min_start_state = state_to_new_name[start_state]

        # Determine the final states of the minimized automaton
        min_final_states = sorted(
            list({state_to_new_name[f] for f in final_states}),
            key=self.state_sort_key
        )

        # Step 8: Construct the minimized transition table
        # Deduplicate and record transitions between minimized states
        minimized_transitions = []
        seen_transitions = set()

        for new_state in sorted_new_states:
            # Find an original state belonging to this equivalence class
            orig_member = None
            for member, name in state_to_new_name.items():
                if name == new_state:
                    orig_member = member
                    break

            # Create transition for each symbol in the alphabet
            for sym in alphabet:
                target_orig = transition_table[orig_member][sym]
                target_new = state_to_new_name[target_orig]
                trans = (new_state, sym, target_new)
                # Ensure no duplicate transitions are added
                if trans not in seen_transitions:
                    seen_transitions.add(trans)
                    minimized_transitions.append(trans)

        # Sort transitions: first by source state, then by symbol, then by target state
        minimized_transitions.sort(
            key=lambda t: (self.state_sort_key(t[0]), t[1], self.state_sort_key(t[2]))
        )

        # Preserve the unique alphabet symbols preserving input order
        unique_alphabet = []
        for sym in alphabet:
            if sym not in unique_alphabet:
                unique_alphabet.append(sym)

        return (
            sorted_new_states,
            unique_alphabet,
            min_start_state,
            min_final_states,
            minimized_transitions
        )

    def run(self, args):
        # Retrieve input and output file paths from command-line arguments
        input_file = args.input
        output_file = args.output

        # Read and validate the input DFA
        (
            states,
            alphabet,
            start_state,
            final_states,
            transitions
        ) = self.read_automaton(input_file)

        # Minimize the DFA using the table-filling algorithm
        (
            min_states,
            min_alphabet,
            min_start_state,
            min_final_states,
            min_transitions
        ) = self.minimize(
            states,
            alphabet,
            start_state,
            final_states,
            transitions
        )

        # Build output lines according to specified format
        output_lines = [
            ' '.join(min_states),
            ' '.join(min_alphabet),
            min_start_state,
            ' '.join(min_final_states),
        ]

        # Append each transition to the output lines
        for src, sym, dst in min_transitions:
            output_lines.append(f"{src} {sym} {dst}")

        # Write the minimized automaton to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines) + '\n')
