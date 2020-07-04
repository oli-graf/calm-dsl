"""
Calm DSL Sample Runbook used for testing runbook pause and play

"""

from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task


code = '''print "Start"
sleep(20)
print "End"'''


@runbook
def DslPausePlayRunbook():
    "Runbook Service example"
    Task.Exec.escript(name="Task1", script=code)
    Task.Exec.escript(name="Task2", script=code)
    Task.Exec.escript(name="Task3", script=code)
    Task.Exec.escript(name="Task4", script=code)
    Task.Exec.escript(name="Task5", script=code)


def main():
    print(DslPausePlayRunbook.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
