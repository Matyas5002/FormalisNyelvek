import argparse
import re
import sys
from collections import Counter

try:
    from project.problem import Problem
except ImportError:
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from project.problem import Problem


class RGX(Problem):
    """
    4. feladat: Logfajl elemzese regularis kifejezesek segitsegevel.
    """

    # Android logcat threadtime sor illesztesere hasznalt kifejezes:
    # 1: teljes fejleces sor
    # 2: datum es ido (pl. '10-15 10:18:51.254')
    # 3: Process ID (PID)
    # 4: Thread ID (TID)
    # 5: Log szint (I, D, V, E, F, A, W)
    # 6: Tag
    # 7: Uzenet (message)
    LOGCAT_PATTERN = re.compile(
        r'(([0-9-]+ [0-9:.]+) +([0-9]+) +([0-9]+) ([IDVEFAW]) (.+?):(?: (.+))?)'
    )

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        A parser inicializalasa a feladathoz tartozo argumentummal.
        """
        parser.add_argument(
            '--rgx',
            help='a regex feladat sorszama (1-5)',
            type=int
        )

    def is_chosen_problem(self, args):
        """
        Annak ellenorzese, hogy a regex feladatot valasztottak-e.
        """
        return args.rgx is not None

    def task1(self, lines):
        """
        1. feladat (--rgx 1):
        Sorok megszamolasa kulonbozo regex feltetelek szerint.
        """
        patterns = [
            # 1. az osszes sort, amelyik 10. honap 15-en jott letre
            re.compile(r'^10-15\b'),
            # 2. az osszes sort, amelyik 10. honap 15-en 10 ora 18 perc es 51 masodperckor jott letre
            re.compile(r'^10-15 10:18:51\b'),
            # 3. az osszes sort, amelyik 51 masodperckor jott letre (mindegy a perc)
            re.compile(r'^[0-9-]+ [0-9]{2}:[0-9]{2}:51\.'),
            # 4. az osszes lowmemorykiller taget tartalmazo sor
            re.compile(r'^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ [IDVEFAW] +lowmemorykiller\s*:'),
            # 5. az osszes 10:18:51-kor keletkezo 221-es process id-ju sor
            re.compile(r'^[0-9-]+ 10:18:51\.[0-9]+ +221 +'),
            # 6. az osszes hibat tartalmazo sor (E)
            re.compile(r'^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ +E '),
            # 7. az osszes warningot (W), amit a PackageManager kuld
            re.compile(r'^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ +W +PackageManager\b'),
            # 8. az osszes ExoPlayer-es debug (D) infot
            re.compile(r'^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ +D +.*ExoPlayer'),
            # 9. az osszes java allomany poziciot tartalmazo hibat es warningot (EW .java:)
            re.compile(r'^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ +[EW] +.*\.java:'),
            # 10. az osszes olyan sort, ami tartalmazza a Thread szot a message reszben (nem a tagben)
            re.compile(r'^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ +[IDVEFAW] +.+?:.*Thread')
        ]

        counts = [
            str(sum(1 for line in lines if pat.search(line)))
            for pat in patterns
        ]
        return '\n'.join(counts)

    def task2(self, lines):
        """
        2. feladat (--rgx 2):
        Az osszes hiba (E sorok) szarmazasi helyet (stack trace, pl. HashMap.java).
        Minden hibasorbol kulon ki kell szedni ezeket az elofordulasuk sorrendjeben.
        """
        java_regex = re.compile(r'\(([a-zA-Z0-9_$.-]+\.java)(?::\d+)?\)')
        extracted = []

        for line in lines:
            m = self.LOGCAT_PATTERN.match(line)
            if m:
                level = m.group(5)
                message = m.group(7) or ''
                if level == 'E':
                    for match in java_regex.finditer(message):
                        extracted.append(match.group(1))

        return '\n'.join(extracted)

    def task3(self, lines):
        """
        3. feladat (--rgx 3):
        Az osszes kulonbozo process id-t megtartva ezek elofordulasi sorrendjet.
        """
        pids = []
        seen = set()

        for line in lines:
            m = self.LOGCAT_PATTERN.match(line)
            if m:
                pid = m.group(3)
                if pid not in seen:
                    seen.add(pid)
                    pids.append(pid)

        return '\n'.join(pids)

    def task4(self, lines):
        """
        4. feladat (--rgx 4):
        A legtobb errort tartalmazo process (PID=xx (xx errors)).
        """
        error_counts = Counter()

        for line in lines:
            m = self.LOGCAT_PATTERN.match(line)
            if m:
                level = m.group(5)
                if level == 'E':
                    pid = m.group(3)
                    error_counts[pid] += 1

        if not error_counts:
            return ""

        max_pid, max_count = error_counts.most_common(1)[0]
        return f"PID={max_pid} ({max_count} errors)"

    def task5(self, lines):
        """
        5. feladat (--rgx 5):
        A fo szalon tortent hibak (E) szamat (amikor a PID es TID megegyezik).
        """
        count = 0

        for line in lines:
            m = self.LOGCAT_PATTERN.match(line)
            if m:
                level = m.group(5)
                pid = m.group(3)
                tid = m.group(4)
                if level == 'E' and pid == tid:
                    count += 1

        return str(count)

    def run(self, args):
        """
        A feladat futtatasa a megadott argumentumok alapjan.
        """
        input_file = args.input
        output_file = args.output
        task_num = int(args.rgx)

        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if task_num == 1:
            result = self.task1(lines)
        elif task_num == 2:
            result = self.task2(lines)
        elif task_num == 3:
            result = self.task3(lines)
        elif task_num == 4:
            result = self.task4(lines)
        elif task_num == 5:
            result = self.task5(lines)
        else:
            print(f"Error: Unknown task number {task_num}", file=sys.stderr)
            sys.exit(1)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='input file')
    parser.add_argument('--output', required=True, help='output file')
    problem = RGX()
    problem.initialize_parser(parser)
    args = parser.parse_args()
    problem.run(args)

